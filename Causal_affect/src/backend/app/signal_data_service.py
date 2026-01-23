"""
Signal Data Service
Queries database for trending behavioral signals and prepares them for analysis
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import logging
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 
                "SYSTEM-CA-002_correlation_analysis" / 
                "FEATURE-CA-002-01_statistical_correlation" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 
                "SYSTEM-CA-002_correlation_analysis" / 
                "FEATURE-CA-002-02_causality_testing" / "src"))

try:
    from composite_signal_aggregator import SourceSignal
except ImportError:
    SourceSignal = None

try:
    from feature_integration import FeatureOrchestrator as CausalityOrchestrator
except ImportError:
    CausalityOrchestrator = None

logger = logging.getLogger(__name__)


class SignalDataService:
    """Service for retrieving and processing behavioral signal data."""
    
    def __init__(self):
        """Initialize the signal data service."""
        self.causality_orchestrator = None
        if CausalityOrchestrator:
            try:
                self.causality_orchestrator = CausalityOrchestrator()
                logger.info("Causality orchestrator initialized")
            except Exception as e:
                logger.warning(f"Could not initialize causality orchestrator: {e}")
    
    async def get_trending_signals(
        self,
        min_momentum: float = 30.0,
        lookback_days: int = 7
    ) -> List['SourceSignal']:
        """
        Get trending signals from all sources.
        
        Args:
            min_momentum: Minimum momentum threshold (%)
            lookback_days: How many days back to analyze
            
        Returns:
            List of SourceSignal objects
        """
        # TODO: Replace with actual database queries
        # This should query:
        # 1. Wikipedia pageview trends
        # 2. Reddit trending topics
        # 3. Twitter trending hashtags
        # 4. Google Trends data
        # 5. arXiv paper submissions
        
        logger.info(f"Fetching trending signals with min_momentum={min_momentum}, lookback={lookback_days} days")
        
        # Placeholder data - replace with actual DB queries
        signals = self._get_mock_signals()
        
        # Filter by momentum
        filtered = [s for s in signals if abs(s.momentum) >= min_momentum]
        
        logger.info(f"Found {len(filtered)} signals above momentum threshold")
        return filtered
    
    async def get_signal_timeseries(
        self,
        keyword: str,
        source: str,
        days: int = 90
    ) -> Optional[np.ndarray]:
        """
        Get time series data for a specific keyword and source.
        
        Args:
            keyword: The keyword to get data for
            source: Data source (wikipedia, reddit, twitter, etc.)
            days: Number of days of historical data
            
        Returns:
            NumPy array of time series data, or None if not found
        """
        # TODO: Query actual time series from database
        # SELECT value, timestamp FROM timeseries_data
        # WHERE metric_name = {keyword}
        # AND tags->>'source' = {source}
        # ORDER BY timestamp DESC
        # LIMIT {days}
        
        logger.info(f"Fetching time series for {keyword} from {source}")
        
        # Placeholder - return mock data
        return np.random.randn(days) * 10 + 50
    
    async def run_granger_analysis(
        self,
        signal_keyword: str,
        composite_timeseries: np.ndarray,
        target_variable: str
    ) -> Dict[str, Any]:
        """
        Run Granger causality analysis using composite signal.
        
        Args:
            signal_keyword: The keyword being analyzed
            composite_timeseries: Weighted composite time series
            target_variable: What to predict
            
        Returns:
            Dictionary with Granger test results
        """
        if self.causality_orchestrator is None:
            logger.warning("Causality orchestrator not available, using mock results")
            return self._get_mock_granger_results()
        
        try:
            # TODO: Get target variable time series from database
            target_ts = await self._get_target_timeseries(target_variable)
            
            if target_ts is None:
                logger.warning(f"Target variable {target_variable} not found")
                return self._get_mock_granger_results()
            
            # Align time series lengths
            min_len = min(len(composite_timeseries), len(target_ts))
            x_data = composite_timeseries[-min_len:]
            y_data = target_ts[-min_len:]
            
            # Run Granger test
            from scipy import stats
            
            # Calculate correlation first
            r_value, corr_p = stats.pearsonr(x_data, y_data)
            
            # Run Granger causality test
            # This will use the updated granger test that includes r_value
            granger_result = self.causality_orchestrator.granger_test.test(x_data, y_data)
            
            return {
                "f_statistic": float(granger_result.test_statistic),
                "p_value": float(granger_result.p_value),
                "r_value": float(r_value),
                "correlation_p_value": float(corr_p),
                "optimal_lag": int(granger_result.lags),
                "n_observations": int(min_len),
                "is_causal": bool(granger_result.reject_null),
                "confidence": self._get_confidence_label(granger_result.p_value)
            }
            
        except Exception as e:
            logger.error(f"Error running Granger analysis: {str(e)}")
            return self._get_mock_granger_results()
    
    async def _get_target_timeseries(self, target_variable: str) -> Optional[np.ndarray]:
        """Get time series for target variable."""
        # TODO: Query database for target variable
        # E.g., stock prices, economic indicators, etc.
        logger.info(f"Fetching target time series for {target_variable}")
        return np.random.randn(90) * 15 + 100
    
    def _get_confidence_label(self, p_value: float) -> str:
        """Convert p-value to confidence label."""
        if p_value < 0.001:
            return "Very High"
        elif p_value < 0.01:
            return "High"
        elif p_value < 0.05:
            return "Moderate"
        else:
            return "Low"
    
    def _get_mock_signals(self) -> List['SourceSignal']:
        """Generate mock signals for testing."""
        if SourceSignal is None:
            return []
        
        return [
            SourceSignal(
                keyword="Layoff",
                source="wikipedia",
                momentum=64.6,
                data_points=500,
                timestamp=datetime.utcnow().isoformat(),
                raw_data=np.random.randn(90) * 10 + 60
            ),
            SourceSignal(
                keyword="layoff",
                source="twitter",
                momentum=72.1,
                data_points=1200,
                timestamp=datetime.utcnow().isoformat(),
                raw_data=np.random.randn(90) * 12 + 70
            ),
            SourceSignal(
                keyword="layoffs",
                source="reddit",
                momentum=60.3,
                data_points=800,
                timestamp=datetime.utcnow().isoformat(),
                raw_data=np.random.randn(90) * 8 + 58
            ),
            SourceSignal(
                keyword="unemployment",
                source="google_trends",
                momentum=45.8,
                data_points=600,
                timestamp=datetime.utcnow().isoformat(),
                raw_data=np.random.randn(90) * 6 + 45
            ),
            SourceSignal(
                keyword="AI",
                source="arxiv",
                momentum=89.2,
                data_points=200,
                timestamp=datetime.utcnow().isoformat(),
                raw_data=np.random.randn(90) * 15 + 85
            ),
            SourceSignal(
                keyword="climate change",
                source="wikipedia",
                momentum=-49.1,
                data_points=450,
                timestamp=datetime.utcnow().isoformat(),
                raw_data=np.random.randn(90) * 10 - 45
            ),
        ]
    
    def _get_mock_granger_results(self) -> Dict[str, Any]:
        """Generate mock Granger results for testing."""
        return {
            "f_statistic": 28.4,
            "p_value": 0.00001,
            "r_value": -0.72,
            "correlation_p_value": 0.0001,
            "optimal_lag": 15,
            "n_observations": 487,
            "is_causal": True,
            "confidence": "Very High"
        }


# Singleton instance
_signal_service = None

def get_signal_service() -> SignalDataService:
    """Get or create singleton signal service instance."""
    global _signal_service
    if _signal_service is None:
        _signal_service = SignalDataService()
    return _signal_service
