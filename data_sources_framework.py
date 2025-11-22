"""
Unified Data Sources Framework for Causal Affect Platform
Ensures consistent data quality across all APIs
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DataQualityMetrics:
    """Metrics for data quality validation"""
    source_name: str
    variable_name: str
    total_points: int
    date_range_start: Optional[datetime]
    date_range_end: Optional[datetime]
    missing_months: List[str]
    data_quality_score: float  # 0-100
    has_minimum_points: bool  # >= 24 months
    is_current: bool  # Last data < 30 days old
    

class BaseDataSource(ABC):
    """
    Abstract base class for all data sources.
    Enforces consistency: monthly granularity, minimum 24 months, proper validation
    """
    
    # Configuration
    MINIMUM_MONTHS = 24  # 2 years minimum for valid correlations
    TARGET_MONTHS = 60   # 5 years target for robust analysis
    MAX_AGE_DAYS = 30    # Data older than this is considered stale
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = logging.getLogger(f"DataSource.{source_name}")
        
    @abstractmethod
    def fetch_variable(self, variable_id: str, months: int = TARGET_MONTHS) -> Dict[str, float]:
        """
        Fetch monthly time series data for a variable.
        
        Args:
            variable_id: Unique identifier for the variable
            months: Number of months of historical data to fetch
            
        Returns:
            Dict mapping "YYYY-MM-01" (first of month) to numeric value
            Must return at least MINIMUM_MONTHS of data or raise exception
        """
        pass
    
    @abstractmethod
    def get_available_variables(self) -> List[Tuple[str, str, str]]:
        """
        Get list of all variables this source can provide.
        
        Returns:
            List of (variable_id, display_name, unit) tuples
            e.g., [("AAPL_CLOSE", "AAPL Stock Price", "USD"),
                   ("AAPL_VOLUME", "AAPL Trading Volume", "shares")]
        """
        pass
    
    def validate_data(self, data: Dict[str, float], variable_name: str) -> DataQualityMetrics:
        """
        Validate fetched data meets quality standards.
        
        Args:
            data: Time series data {date_str: value}
            variable_name: Name of variable for logging
            
        Returns:
            DataQualityMetrics object
            
        Raises:
            ValueError if data doesn't meet minimum standards
        """
        if not data:
            raise ValueError(f"{variable_name}: No data returned")
        
        # Sort dates
        dates = sorted(data.keys())
        total_points = len(dates)
        
        # Check minimum requirement
        if total_points < self.MINIMUM_MONTHS:
            raise ValueError(
                f"{variable_name}: Only {total_points} months of data "
                f"(minimum {self.MINIMUM_MONTHS} required)"
            )
        
        # Parse date range
        start_date = datetime.strptime(dates[0], "%Y-%m-%d")
        end_date = datetime.strptime(dates[-1], "%Y-%m-%d")
        
        # Check data currency
        days_old = (datetime.utcnow() - end_date).days
        is_current = days_old < self.MAX_AGE_DAYS
        
        # Identify missing months
        expected_months = self._generate_month_range(start_date, end_date)
        missing_months = [m for m in expected_months if m not in data]
        
        # Calculate quality score
        completeness = (total_points / len(expected_months)) * 100 if expected_months else 0
        currency_bonus = 10 if is_current else 0
        quality_score = min(completeness + currency_bonus, 100)
        
        metrics = DataQualityMetrics(
            source_name=self.source_name,
            variable_name=variable_name,
            total_points=total_points,
            date_range_start=start_date,
            date_range_end=end_date,
            missing_months=missing_months,
            data_quality_score=quality_score,
            has_minimum_points=total_points >= self.MINIMUM_MONTHS,
            is_current=is_current
        )
        
        # Log quality issues
        if missing_months:
            self.logger.warning(
                f"{variable_name}: Missing {len(missing_months)} months of data"
            )
        if not is_current:
            self.logger.warning(
                f"{variable_name}: Data is {days_old} days old (stale)"
            )
        if quality_score < 80:
            self.logger.warning(
                f"{variable_name}: Quality score {quality_score:.1f}/100"
            )
        
        self.logger.info(
            f"{variable_name}: {total_points} points, "
            f"{start_date.strftime('%Y-%m')} to {end_date.strftime('%Y-%m')}, "
            f"quality {quality_score:.1f}/100"
        )
        
        return metrics
    
    def normalize_to_monthly(self, daily_data: Dict[str, float]) -> Dict[str, float]:
        """
        Convert daily data to monthly (end-of-month) values.
        
        Args:
            daily_data: Dict of {date_str: value} with daily granularity
            
        Returns:
            Dict of {first_of_month: end_of_month_value}
        """
        monthly = {}
        
        # Group by year-month
        by_month = {}
        for date_str, value in daily_data.items():
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            month_key = date_obj.strftime("%Y-%m")
            
            if month_key not in by_month:
                by_month[month_key] = []
            by_month[month_key].append((date_obj, value))
        
        # Get last day of each month
        for month_key, values in by_month.items():
            # Sort by date and take last value (end of month)
            values.sort(key=lambda x: x[0])
            last_value = values[-1][1]
            
            # Use first day of month as key for consistency
            first_of_month = f"{month_key}-01"
            monthly[first_of_month] = last_value
        
        return monthly
    
    def fill_missing_months(self, data: Dict[str, float], method: str = "forward") -> Dict[str, float]:
        """
        Fill missing months with interpolated values.
        
        Args:
            data: Time series with possible gaps
            method: "forward" (carry forward), "linear" (interpolate), or "zero"
            
        Returns:
            Complete time series with no gaps
        """
        if not data:
            return data
        
        dates = sorted(data.keys())
        start = datetime.strptime(dates[0], "%Y-%m-%d")
        end = datetime.strptime(dates[-1], "%Y-%m-%d")
        
        # Generate all expected months
        expected = self._generate_month_range(start, end)
        filled = {}
        
        last_value = None
        for month in expected:
            if month in data:
                filled[month] = data[month]
                last_value = data[month]
            elif method == "forward" and last_value is not None:
                filled[month] = last_value
                self.logger.debug(f"Forward-filled {month} with {last_value}")
            elif method == "zero":
                filled[month] = 0.0
            # For "linear" we'd need more complex interpolation
        
        return filled
    
    @staticmethod
    def _generate_month_range(start: datetime, end: datetime) -> List[str]:
        """Generate list of YYYY-MM-01 strings between start and end dates"""
        months = []
        current = start.replace(day=1)
        end_first = end.replace(day=1)
        
        while current <= end_first:
            months.append(current.strftime("%Y-%m-%d"))
            current += relativedelta(months=1)
        
        return months


class DataSourceRegistry:
    """Registry for managing all data sources"""
    
    def __init__(self):
        self.sources: Dict[str, BaseDataSource] = {}
        
    def register(self, source: BaseDataSource):
        """Register a data source"""
        self.sources[source.source_name] = source
        logger.info(f"Registered data source: {source.source_name}")
        
    def get_source(self, source_name: str) -> Optional[BaseDataSource]:
        """Get a registered data source"""
        return self.sources.get(source_name)
    
    def list_sources(self) -> List[str]:
        """List all registered sources"""
        return list(self.sources.keys())
    
    def get_all_variables(self) -> List[Tuple[str, str, str, str]]:
        """
        Get all variables from all sources.
        
        Returns:
            List of (source_name, variable_id, display_name, unit) tuples
        """
        all_vars = []
        for source_name, source in self.sources.items():
            for var_id, display_name, unit in source.get_available_variables():
                all_vars.append((source_name, var_id, display_name, unit))
        return all_vars


# Global registry
registry = DataSourceRegistry()
