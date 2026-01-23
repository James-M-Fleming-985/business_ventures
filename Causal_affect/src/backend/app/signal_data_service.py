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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from scipy import stats

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 
                "SYSTEM-CA-002_correlation_analysis" / 
                "FEATURE-CA-002-01_statistical_correlation" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 
                "SYSTEM-CA-002_correlation_analysis" / 
                "FEATURE-CA-002-02_causality_testing" / "src"))

# Import database models
sys.path.insert(0, str(Path(__file__).parent.parent))
from features.FEATURE_CA_001_03_timeseries_storage.db.schema import timeseries_data_table

try:
    from composite_signal_aggregator import SourceSignal
except ImportError:
    SourceSignal = None

try:
    from feature_integration import FeatureOrchestrator as CausalityOrchestrator
except ImportError:
    CausalityOrchestrator = None

from .config import settings

logger = logging.getLogger(__name__)


class SignalDataService:
    """Service for retrieving and processing behavioral signal data."""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        Initialize the signal data service.
        
        Args:
            db_session: Optional database session. If not provided, queries will fail.
        """
        self.db = db_session
        self.causality_orchestrator = None
        if CausalityOrchestrator:
            try:
                self.causality_orchestrator = CausalityOrchestrator()
                logger.info("Causality orchestrator initialized")
            except Exception as e:
                logger.warning(f"Could not initialize causality orchestrator: {e}")
    
    async def get_trending_signals(
        self,
        min_momentum: float = None,
        lookback_days: int = None
    ) -> List['SourceSignal']:
        """
        Get trending signals from all sources.
        
        Args:
            min_momentum: Minimum momentum threshold (%). Uses config default if None.
            lookback_days: How many days back to analyze. Uses config default if None.
            
        Returns:
            List of SourceSignal objects
        """
        if min_momentum is None:
            min_momentum = settings.signal_min_momentum
        if lookback_days is None:
            lookback_days = settings.signal_lookback_days
            
        if self.db is None:
            logger.error("No database session available")
            return []
        
        if SourceSignal is None:
            logger.error("SourceSignal class not available")
            return []
        
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=lookback_days)
            
            # Query for signals with momentum calculation
            # Get all metric_name + source combinations with their data
            query = select(
                timeseries_data_table.c.metric_name,
                timeseries_data_table.c.tags['source'].label('source'),
                func.count().label('data_points'),
                func.array_agg(
                    timeseries_data_table.c.value
                ).label('values'),
                func.array_agg(
                    timeseries_data_table.c.timestamp
                ).label('timestamps')
            ).where(
                and_(
                    timeseries_data_table.c.timestamp >= start_time,
                    timeseries_data_table.c.timestamp <= end_time,
                    timeseries_data_table.c.tags.has_key('source')
                )
            ).group_by(
                timeseries_data_table.c.metric_name,
                timeseries_data_table.c.tags['source']
            ).having(
                func.count() >= settings.signal_min_data_points
            )
            
            result = await self.db.execute(query)
            rows = result.fetchall()
            
            signals = []
            for row in rows:
                # Calculate momentum from values
                values = np.array(row.values)
                if len(values) < 2:
                    continue
                
                # Momentum = % change from first to last value
                first_val = values[0]
                last_val = values[-1]
                
                if first_val != 0:
                    momentum = ((last_val - first_val) / abs(first_val)) * 100
                else:
                    momentum = 0 if last_val == 0 else 100
                
                # Filter by minimum momentum
                if abs(momentum) >= min_momentum:
                    signals.append(SourceSignal(
                        keyword=row.metric_name,
                        source=row.source or "unknown",
                        momentum=float(momentum),
                        data_points=int(row.data_points),
                        timestamp=datetime.utcnow().isoformat(),
                        raw_data=values
                    ))
            
            logger.info(f"Found {len(signals)} signals above momentum threshold {min_momentum}%")
            return signals
            
        except Exception as e:
            logger.error(f"Error fetching trending signals: {str(e)}")
            return []
    
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
        if self.db is None:
            logger.error("No database session available")
            return None
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            # Query for specific keyword and source
            query = select(
                timeseries_data_table.c.value,
                timeseries_data_table.c.timestamp
            ).where(
                and_(
                    timeseries_data_table.c.metric_name == keyword,
                    timeseries_data_table.c.tags['source'].astext == source,
                    timeseries_data_table.c.timestamp >= start_time,
                    timeseries_data_table.c.timestamp <= end_time
                )
            ).order_by(
                timeseries_data_table.c.timestamp.asc()
            )
            
            result = await self.db.execute(query)
            rows = result.fetchall()
            
            if not rows:
                logger.warning(f"No data found for {keyword} from {source}")
                return None
            
            values = np.array([row.value for row in rows])
            logger.info(f"Retrieved {len(values)} data points for {keyword} from {source}")
            return values
            
        except Exception as e:
            logger.error(f"Error fetching time series for {keyword}/{source}: {str(e)}")
            return None
    
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
            logger.warning("Causality orchestrator not available")
            return self._get_error_granger_results("Granger test not available")
        
        try:
            # Get target variable time series from database
            target_ts = await self._get_target_timeseries(target_variable)
            
            if target_ts is None:
                logger.warning(f"Target variable {target_variable} not found")
                return self._get_error_granger_results(f"Target variable '{target_variable}' not found in database")
            
            # Align time series lengths
            min_len = min(len(composite_timeseries), len(target_ts))
            
            if min_len < settings.granger_min_observations:
                logger.warning(f"Insufficient data: {min_len} < {settings.granger_min_observations}")
                return self._get_error_granger_results(f"Insufficient data points: {min_len} (need at least {settings.granger_min_observations})")
            
            x_data = composite_timeseries[-min_len:]
            y_data = target_ts[-min_len:]
            
            # Calculate correlation first
            r_value, corr_p = stats.pearsonr(x_data, y_data)
            
            # Run Granger causality test
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
            return self._get_error_granger_results(f"Error: {str(e)}")
    
    async def _get_target_timeseries(self, target_variable: str) -> Optional[np.ndarray]:
        """Get time series for target variable."""
        if self.db is None:
            return None
        
        try:
            # Query for target variable (could be stock prices, unemployment, etc.)
            # Target variables are stored with tags->>'type' = 'target'
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=90)
            
            query = select(
                timeseries_data_table.c.value
            ).where(
                and_(
                    timeseries_data_table.c.metric_name == target_variable,
                    timeseries_data_table.c.tags['type'].astext == 'target',
                    timeseries_data_table.c.timestamp >= start_time,
                    timeseries_data_table.c.timestamp <= end_time
                )
            ).order_by(
                timeseries_data_table.c.timestamp.asc()
            )
            
            result = await self.db.execute(query)
            rows = result.fetchall()
            
            if not rows:
                logger.warning(f"No target data found for {target_variable}")
                return None
            
            values = np.array([row.value for row in rows])
            logger.info(f"Retrieved {len(values)} target data points for {target_variable}")
            return values
            
        except Exception as e:
            logger.error(f"Error fetching target time series: {str(e)}")
            return None
    
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
    
    def _get_error_granger_results(self, error_message: str) -> Dict[str, Any]:
        """Generate error response for Granger test."""
        return {
            "f_statistic": 0.0,
            "p_value": 1.0,
            "r_value": 0.0,
            "correlation_p_value": 1.0,
            "optimal_lag": 0,
            "n_observations": 0,
            "is_causal": False,
            "confidence": "None",
            "error": error_message
        }


# Singleton instance - now requires db session
def get_signal_service(db: AsyncSession) -> SignalDataService:
    """Get signal service instance with database session."""
    return SignalDataService(db_session=db)
