"""
Data Alignment and Normalization Utilities

Ensures consistent data universe across all data sources by:
1. Normalizing all dates to first-of-month standard grid
2. Interpolating/forward-filling missing values
3. Handling different API date formats and ranges

This allows seamless correlation analysis across diverse data sources.
"""

from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def get_standard_monthly_grid(months_back: int = 60) -> List[datetime]:
    """
    Generate standard monthly date grid (first of month).
    
    Args:
        months_back: Number of months to include (default 60 = 5 years)
    
    Returns:
        List of datetime objects, oldest to newest
        Example: [2020-12-01, 2021-01-01, ..., 2025-11-01]
    """
    today = datetime.now()
    # Most recent complete month
    end_date = today.replace(day=1)
    if today.day < 5:  # If early in month, use previous month
        end_date = (end_date - pd.DateOffset(months=1))
    
    # Generate monthly grid
    dates = pd.date_range(
        end=end_date,
        periods=months_back,
        freq='MS'  # Month Start
    )
    
    return dates.to_pydatetime().tolist()


def normalize_to_standard_grid(
    raw_data: Dict[str, float],
    standard_grid: List[datetime],
    fill_method: str = 'ffill'
) -> Dict[str, float]:
    """
    Normalize arbitrary monthly data to standard grid with gap filling.
    
    Args:
        raw_data: {date_string: value} from API (any format)
        standard_grid: List of standard datetime objects
        fill_method: 'ffill' (forward-fill), 'interpolate', or 'none'
    
    Returns:
        {date_string: value} aligned to standard grid
    """
    if not raw_data:
        return {}
    
    # Parse raw data into DataFrame with normalized dates
    parsed_data = []
    for date_str, value in raw_data.items():
        try:
            # Try multiple date formats
            for fmt in ["%Y-%m-%d", "%Y-%m", "%Y/%m/%d", "%m/%d/%Y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                # If no format works, try pandas parser
                dt = pd.to_datetime(date_str)
            
            # Normalize to first of month
            month_start = dt.replace(day=1, hour=0, minute=0, second=0)
            parsed_data.append({'date': month_start, 'value': float(value)})
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            continue
    
    if not parsed_data:
        return {}
    
    # Create DataFrame
    df = pd.DataFrame(parsed_data)
    df = df.drop_duplicates(subset=['date']).set_index('date').sort_index()
    
    # Create standard grid DataFrame
    grid_df = pd.DataFrame({'date': standard_grid})
    grid_df = grid_df.set_index('date')
    
    # Merge with standard grid
    merged = grid_df.join(df, how='left')
    
    # Apply fill method
    if fill_method == 'ffill':
        # Forward fill (repeat last known value)
        merged['value'] = merged['value'].fillna(method='ffill')
    elif fill_method == 'interpolate':
        # Linear interpolation
        merged['value'] = merged['value'].interpolate(method='linear')
    elif fill_method == 'bfill':
        # Backward fill
        merged['value'] = merged['value'].fillna(method='bfill')
    # 'none' leaves NaN as-is
    
    # Convert back to dict (only non-NaN values)
    result = {}
    for date, value in merged['value'].items():
        if pd.notna(value):
            result[date.strftime("%Y-%m-%d")] = float(value)
    
    return result


def get_fill_strategy_for_variable_type(source: str, variable_name: str) -> str:
    """
    Determine best fill strategy based on variable type.
    
    Returns:
        'ffill', 'interpolate', or 'none'
    """
    # Economic indicators: forward fill (values change slowly)
    if source in ['worldbank', 'fred']:
        return 'ffill'
    
    # Stock prices: interpolate (smooth transitions)
    if source == 'alpha_vantage':
        return 'interpolate'
    
    # Event counts: forward fill with zero
    if source in ['usgs', 'nasa_eonet']:
        return 'ffill'
    
    # Paper counts: interpolate
    if source == 'arxiv':
        return 'interpolate'
    
    # Clinical trials: forward fill
    if source == 'clinicaltrials':
        return 'ffill'
    
    # Default: forward fill (conservative)
    return 'ffill'


# Usage example:
if __name__ == "__main__":
    std_dates = get_standard_monthly_dates(60)
    print(f"Standard date range: {len(std_dates)} months")
    print(f"From: {std_dates[-1].strftime('%Y-%m-%d')}")
    print(f"To: {std_dates[0].strftime('%Y-%m-%d')}")
    print(f"\\nFirst 5 dates:")
    for d in std_dates[:5]:
        print(f"  {d.strftime('%Y-%m-%d')}")
