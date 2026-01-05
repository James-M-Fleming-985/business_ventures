"""
Granger Causality Service for Causal Affect Platform
Integrates Granger causality testing with correlation analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from datetime import datetime
import logging

# Import the existing Granger implementation
import sys
from pathlib import Path
causal_affect_path = Path(__file__).parent.parent / "Causal_affect" / "SYSTEM-CA-002_correlation_analysis" / "FEATURE-CA-002-02_causality_testing" / "LAYER-CA-002-02-01_granger_test" / "src"
sys.path.insert(0, str(causal_affect_path))
from implementation import GrangerCausalityTest, GrangerTestResult

from database import get_db_session
from models import TimeSeriesData, VariableMetadata, CorrelationResult

logger = logging.getLogger(__name__)


class GrangerCausalityService:
    """
    Service for testing Granger causality between correlated variables
    """
    
    def __init__(self, max_lag: int = 12, confidence_level: float = 0.05):
        """
        Initialize Granger causality service
        
        Args:
            max_lag: Maximum lag to test (default: 12 months)
            confidence_level: Significance threshold (default: 0.05)
        """
        self.granger_tester = GrangerCausalityTest(
            max_lag=max_lag,
            confidence_level=confidence_level,
            handle_missing='drop'
        )
        
    def test_causality(self, var1_id: int, var2_id: int, 
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> Dict:
        """
        Test Granger causality between two variables in both directions
        
        Args:
            var1_id: ID of first variable
            var2_id: ID of second variable
            start_date: Optional start date for data filtering
            end_date: Optional end date for data filtering
            
        Returns:
            Dictionary with bidirectional causality results
        """
        with get_db_session() as session:
            # Get variable metadata
            var1 = session.query(VariableMetadata).filter_by(id=var1_id).first()
            var2 = session.query(VariableMetadata).filter_by(id=var2_id).first()
            
            if not var1 or not var2:
                raise ValueError(f"Variables not found: {var1_id}, {var2_id}")
            
            # Build query filters
            filters_var1 = [TimeSeriesData.variable_id == var1_id]
            filters_var2 = [TimeSeriesData.variable_id == var2_id]
            
            if start_date:
                filters_var1.append(TimeSeriesData.timestamp >= start_date)
                filters_var2.append(TimeSeriesData.timestamp >= start_date)
                
            if end_date:
                filters_var1.append(TimeSeriesData.timestamp <= end_date)
                filters_var2.append(TimeSeriesData.timestamp <= end_date)
            
            # Fetch time series data
            var1_data = session.query(TimeSeriesData).filter(*filters_var1).order_by(TimeSeriesData.timestamp).all()
            var2_data = session.query(TimeSeriesData).filter(*filters_var2).order_by(TimeSeriesData.timestamp).all()
            
            # Convert to pandas Series for alignment and interpolation
            var1_series = pd.Series(
                index=[dp.timestamp for dp in var1_data],
                data=[dp.value for dp in var1_data]
            )
            var2_series = pd.Series(
                index=[dp.timestamp for dp in var2_data],
                data=[dp.value for dp in var2_data]
            )
            
            logger.info(f"Raw data counts: {var1.display_name}={len(var1_data)}, {var2.display_name}={len(var2_data)}")
            
            # Align time series with pandas interpolation (handles different frequencies)
            aligned_data = pd.DataFrame({
                'var1': var1_series,
                'var2': var2_series
            })
            
            # Sort by timestamp
            aligned_data = aligned_data.sort_index()
            
            # Interpolate missing values using time-based interpolation
            aligned_data = aligned_data.interpolate(method='time', limit_direction='both')
            
            # Drop any remaining NaN values
            aligned_data = aligned_data.dropna()
            
            # Check if we have enough aligned data
            if len(aligned_data) < self.granger_tester.max_lag + 10:
                raise ValueError(
                    f"Insufficient aligned data after interpolation: {len(aligned_data)} points "
                    f"(need {self.granger_tester.max_lag + 10}). "
                    f"Raw counts: {var1.display_name}={len(var1_data)}, {var2.display_name}={len(var2_data)}"
                )
            
            # Extract aligned values
            var1_values = aligned_data['var1'].values
            var2_values = aligned_data['var2'].values
            common_timestamps = aligned_data.index.tolist()
            
            logger.info(f"Testing Granger causality: {var1.display_name} ↔ {var2.display_name} "
                       f"with {len(common_timestamps)} aligned data points")
            
            # Test bidirectional causality
            results = self.granger_tester.test_bidirectional(var1_values, var2_values)
            
            # Interpret results
            xy_result = results['x_causes_y']  # var1 → var2
            yx_result = results['y_causes_x']  # var2 → var1
            
            # Determine overall causal direction
            direction = self._determine_direction(xy_result, yx_result)
            
            return {
                'var1': {
                    'id': var1_id,
                    'name': var1.display_name
                },
                'var2': {
                    'id': var2_id,
                    'name': var2.display_name
                },
                'var1_to_var2': {
                    'p_value': xy_result.p_value,
                    'test_statistic': xy_result.test_statistic,
                    'lags': xy_result.lags,
                    'significant': xy_result.reject_null,
                    'interpretation': self._interpret_result(var1.display_name, var2.display_name, xy_result)
                },
                'var2_to_var1': {
                    'p_value': yx_result.p_value,
                    'test_statistic': yx_result.test_statistic,
                    'lags': yx_result.lags,
                    'significant': yx_result.reject_null,
                    'interpretation': self._interpret_result(var2.display_name, var1.display_name, yx_result)
                },
                'causal_direction': direction,
                'sample_size': len(common_timestamps),
                'date_range': {
                    'start': common_timestamps[0].strftime('%Y-%m-%d'),
                    'end': common_timestamps[-1].strftime('%Y-%m-%d')
                },
                'explanation': self._generate_explanation(var1.display_name, var2.display_name, 
                                                         xy_result, yx_result, direction)
            }
    
    def _determine_direction(self, xy_result: GrangerTestResult, 
                            yx_result: GrangerTestResult) -> str:
        """
        Determine overall causal direction from bidirectional test results
        
        Returns: 'x_to_y', 'y_to_x', 'bidirectional', or 'none'
        """
        xy_significant = xy_result.reject_null
        yx_significant = yx_result.reject_null
        
        if xy_significant and yx_significant:
            # Both directions significant - choose stronger one or mark bidirectional
            if abs(xy_result.p_value - yx_result.p_value) < 0.01:
                return 'bidirectional'
            elif xy_result.p_value < yx_result.p_value:
                return 'x_to_y'
            else:
                return 'y_to_x'
        elif xy_significant:
            return 'x_to_y'
        elif yx_significant:
            return 'y_to_x'
        else:
            return 'none'
    
    def _interpret_result(self, cause_name: str, effect_name: str, 
                         result: GrangerTestResult) -> str:
        """Generate natural language interpretation of result"""
        if result.reject_null:
            return (f"{cause_name} Granger-causes {effect_name} "
                   f"(p = {result.p_value:.4f}, lag = {result.lags}). "
                   f"Past values of {cause_name} help predict {effect_name}.")
        else:
            return (f"No Granger causality detected from {cause_name} to {effect_name} "
                   f"(p = {result.p_value:.4f}). "
                   f"Past values of {cause_name} do not significantly improve predictions of {effect_name}.")
    
    def _generate_explanation(self, var1_name: str, var2_name: str,
                             xy_result: GrangerTestResult, yx_result: GrangerTestResult,
                             direction: str) -> str:
        """Generate comprehensive explanation of causality findings"""
        
        if direction == 'x_to_y':
            return (f"<b>Unidirectional Causality Detected:</b> {var1_name} → {var2_name}<br><br>"
                   f"{var1_name} Granger-causes {var2_name} (p = {xy_result.p_value:.4f}) with a "
                   f"{xy_result.lags}-period lag. This means past values of {var1_name} contain "
                   f"information that helps predict future values of {var2_name}, beyond what can "
                   f"be predicted from {var2_name}'s own history.<br><br>"
                   f"<b>Trading Implication:</b> Changes in {var1_name} may provide early signals "
                   f"for anticipated changes in {var2_name} approximately {xy_result.lags} periods later.")
        
        elif direction == 'y_to_x':
            return (f"<b>Unidirectional Causality Detected:</b> {var2_name} → {var1_name}<br><br>"
                   f"{var2_name} Granger-causes {var1_name} (p = {yx_result.p_value:.4f}) with a "
                   f"{yx_result.lags}-period lag. This means past values of {var2_name} contain "
                   f"information that helps predict future values of {var1_name}, beyond what can "
                   f"be predicted from {var1_name}'s own history.<br><br>"
                   f"<b>Trading Implication:</b> Changes in {var2_name} may provide early signals "
                   f"for anticipated changes in {var1_name} approximately {yx_result.lags} periods later.")
        
        elif direction == 'bidirectional':
            return (f"<b>Bidirectional Causality Detected:</b> {var1_name} ↔ {var2_name}<br><br>"
                   f"Both variables Granger-cause each other:<br>"
                   f"• {var1_name} → {var2_name} (p = {xy_result.p_value:.4f}, lag = {xy_result.lags})<br>"
                   f"• {var2_name} → {var1_name} (p = {yx_result.p_value:.4f}, lag = {yx_result.lags})<br><br>"
                   f"This feedback relationship suggests the variables mutually influence each other. "
                   f"Changes in either variable provide information about future changes in the other.<br><br>"
                   f"<b>Trading Implication:</b> This feedback loop may create momentum effects or "
                   f"oscillating patterns. Monitor both variables for trading signals.")
        
        else:  # no causality
            return (f"<b>No Granger Causality Detected</b><br><br>"
                   f"Neither variable Granger-causes the other at the {xy_result.confidence_level} significance level:<br>"
                   f"• {var1_name} → {var2_name} (p = {xy_result.p_value:.4f})<br>"
                   f"• {var2_name} → {var1_name} (p = {yx_result.p_value:.4f})<br><br>"
                   f"While these variables are correlated, past values of one do not significantly "
                   f"improve predictions of the other. The correlation may be due to a common driving "
                   f"factor rather than direct causal influence.<br><br>"
                   f"<b>Trading Implication:</b> Exercise caution. The correlation alone may not be "
                   f"actionable for predictive trading strategies.")
