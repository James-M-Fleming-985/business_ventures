```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Calculator for user engagement metrics including DAU, MAU, and retention rates.
    """

    def __init__(self):
        """Initialize the MetricsCalculator."""
        self.sessions = []
        self.users = set()
        self._session_cache = {}
        self._dau_cache = {}
        self._mau_cache = {}

    def add_session(self, user_id: str, timestamp: Union[str, datetime], 
                   session_id: Optional[str] = None, 
                   duration: Optional[int] = None,
                   metadata: Optional[Dict] = None) -> None:
        """
        Add a session record.

        Args:
            user_id: Unique identifier for the user
            timestamp: Session timestamp
            session_id: Optional session identifier
            duration: Optional session duration in seconds
            metadata: Optional additional session metadata
        """
        if not user_id:
            logger.warning("Session with empty user_id ignored")
            return

        if isinstance(timestamp, str):
            try:
                timestamp = pd.to_datetime(timestamp)
            except Exception as e:
                logger.error(f"Invalid timestamp format: {timestamp}, error: {e}")
                return

        session = {
            'user_id': user_id,
            'timestamp': timestamp,
            'session_id': session_id or f"{user_id}_{timestamp.isoformat()}",
            'duration': duration or 0,
            'metadata': metadata or {}
        }

        self.sessions.append(session)
        self.users.add(user_id)
        
        # Invalidate caches
        self._dau_cache = {}
        self._mau_cache = {}

    def calculate_dau(self, date: Union[str, datetime]) -> int:
        """
        Calculate Daily Active Users for a specific date.

        Args:
            date: Date to calculate DAU for

        Returns:
            Number of unique active users on that date
        """
        if isinstance(date, str):
            date = pd.to_datetime(date)

        date_key = date.date()
        
        if date_key in self._dau_cache:
            return self._dau_cache[date_key]

        if not self.sessions:
            return 0

        active_users = set()
        for session in self.sessions:
            session_date = session['timestamp'].date()
            if session_date == date_key:
                active_users.add(session['user_id'])

        dau = len(active_users)
        self._dau_cache[date_key] = dau
        return dau

    def calculate_mau(self, date: Union[str, datetime]) -> int:
        """
        Calculate Monthly Active Users for the 30 days preceding and including the date.

        Args:
            date: End date for MAU calculation

        Returns:
            Number of unique active users in the 30-day period
        """
        if isinstance(date, str):
            date = pd.to_datetime(date)

        date_key = date.date()
        
        if date_key in self._mau_cache:
            return self._mau_cache[date_key]

        if not self.sessions:
            return 0

        start_date = (date - timedelta(days=29)).date()
        end_date = date_key

        active_users = set()
        for session in self.sessions:
            session_date = session['timestamp'].date()
            if start_date <= session_date <= end_date:
                active_users.add(session['user_id'])

        mau = len(active_users)
        self._mau_cache[date_key] = mau
        return mau

    def calculate_retention_rate(self, cohort_date: Union[str, datetime], 
                                 period_days: int) -> float:
        """
        Calculate retention rate for a cohort after a specific period.

        Args:
            cohort_date: Date defining the cohort (users active on this date)
            period_days: Number of days after cohort_date to measure retention

        Returns:
            Retention rate as a decimal (0.0 to 1.0)
        """
        if isinstance(cohort_date, str):
            cohort_date = pd.to_datetime(cohort_date)

        if not self.sessions:
            return 0.0

        cohort_date_key = cohort_date.date()
        target_date = (cohort_date + timedelta(days=period_days)).date()

        # Get cohort users (users active on cohort_date)
        cohort_users = set()
        for session in self.sessions:
            if session['timestamp'].date() == cohort_date_key:
                cohort_users.add(session['user_id'])

        if not cohort_users:
            return 0.0

        # Get retained users (cohort users active on target_date)
        retained_users = set()
        for session in self.sessions:
            if session['timestamp'].date() == target_date:
                if session['user_id'] in cohort_users:
                    retained_users.add(session['user_id'])

        retention_rate = len(retained_users) / len(cohort_users)
        return retention_rate

    def get_cohort_retention_matrix(self, start_date: Union[str, datetime],
                                   end_date: Union[str, datetime],
                                   periods: List[int]) -> pd.DataFrame:
        """
        Generate a retention matrix for multiple cohorts and periods.

        Args:
            start_date: Start date for cohort analysis
            end_date: End date for cohort analysis
            periods: List of period days to calculate retention for

        Returns:
            DataFrame with cohorts as rows and periods as columns
        """
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)

        cohort_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        retention_data = {}
        for period in periods:
            retention_data[f'day_{period}'] = []

        cohort_list = []
        
        for cohort_date in cohort_dates:
            cohort_list.append(cohort_date.date())
            for period in periods:
                rate = self.calculate_retention_rate(cohort_date, period)
                retention_data[f'day_{period}'].append(rate)

        df = pd.DataFrame(retention_data, index=cohort_list)
        df.index.name = 'cohort_date'
        return df

    def get_sessions_df(self) -> pd.DataFrame:
        """
        Get all sessions as a DataFrame.

        Returns:
            DataFrame containing all session data
        """
        if not self.sessions:
            return pd.DataFrame(columns=['user_id', 'timestamp', 'session_id', 'duration'])

        df = pd.DataFrame(self.sessions)
        return df

    def calculate_engagement_metrics(self, date: Union[str, datetime]) -> Dict:
        """
        Calculate comprehensive engagement metrics for a specific date.

        Args:
            date: Date to calculate metrics for

        Returns:
            Dictionary containing DAU, MAU, and DAU/MAU ratio
        """
        if isinstance(date, str):
            date = pd.to_datetime(date)

        dau = self.calculate_dau(date)
        mau = self.calculate_mau(date)
        
        dau_mau_ratio = dau / mau if mau > 0 else 0.0

        return {
            'date': date.date(),
            'dau': dau,
            'mau': mau,
            'dau_mau_ratio': dau_mau_ratio
        }

    def calculate_cohort_size(self, cohort_date: Union[str, datetime]) -> int:
        """
        Calculate the size of a cohort (users active on a specific date).

        Args:
            cohort_date: Date defining the cohort

        Returns:
            Number of unique users in the cohort
        """
        if isinstance(cohort_date, str):
            cohort_date = pd.to_datetime(cohort_date)

        cohort_date_key = cohort_date.date()

        cohort_users = set()
        for session in self.sessions:
            if session['timestamp'].date() == cohort_date_key:
                cohort_users.add(session['user_id'])

        return len(cohort_users)

    def get_active_users_by_period(self, start_date: Union[str, datetime],
                                   end_date: Union[str, datetime]) -> Dict[str, Set[str]]:
        """
        Get active users grouped by date for a period.

        Args:
            start_date: Start date of the period
            end_date: End date of the period

        Returns:
            Dictionary mapping date strings to sets of active user IDs
        """
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)

        start_key = start_date.date()
        end_key = end_date.date()

        active_by_date = defaultdict(set)
        
        for session in self.sessions:
            session_date = session['timestamp'].date()
            if start_key <= session_date <= end_key:
                active_by_date[str(session_date)].add(session['user_id'])

        return dict(active_by_date)

    def clear_sessions(self) -> None:
        """Clear all session data and caches."""
        self.sessions = []
        self.users = set()
        self._session_cache = {}
        self._dau_cache = {}
        self._mau_cache = {}

    def get_user_session_count(self, user_id: str, 
                              start_date: Optional[Union[str, datetime]] = None,
                              end_date: Optional[Union[str, datetime]] = None) -> int:
        """
        Get the number of sessions for a specific user in a date range.

        Args:
            user_id: User identifier
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Number of sessions for the user
        """
        if start_date and isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if end_date and isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)

        count = 0
        for session in self.sessions:
            if session['user_id'] != user_id:
                continue
            
            if start_date and session['timestamp'] < start_date:
                continue
            
            if end_date and session['timestamp'] > end_date:
                continue
            
            count += 1

        return count

    def calculate_average_session_duration(self, date: Union[str, datetime]) -> float:
        """
        Calculate average session duration for a specific date.

        Args:
            date: Date to calculate average for

        Returns:
            Average session duration in seconds
        """
        if isinstance(date, str):
            date = pd.to_datetime(date)

        date_key = date.date()
        
        durations = []
        for session in self.sessions:
            if session['timestamp'].date() == date_key:
                if session.get('duration') is not None:
                    durations.append(session['duration'])

        if not durations:
            return 0.0

        return sum(durations) / len(durations)
```