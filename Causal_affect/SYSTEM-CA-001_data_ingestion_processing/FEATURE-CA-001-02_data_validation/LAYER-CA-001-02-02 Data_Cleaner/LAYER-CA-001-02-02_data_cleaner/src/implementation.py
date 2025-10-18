```python
import pandas as pd
import numpy as np
from typing import Union, List, Dict, Any, Optional
import warnings


class DataCleaner:
    """
    A class for cleaning and preprocessing data while preserving missing values.
    
    This class provides methods to handle missing values without data loss,
    ensuring that the original data structure and information is maintained.
    """
    
    def __init__(self):
        """Initialize the DataCleaner."""
        self._missing_value_map = {}
        self._original_dtypes = {}
        
    def clean_data(self, data: Union[pd.DataFrame, pd.Series, List, Dict, np.ndarray]) -> Union[pd.DataFrame, pd.Series, List, Dict, np.ndarray]:
        """
        Clean data while preserving missing values.
        
        Args:
            data: Input data to be cleaned (DataFrame, Series, list, dict, or array)
            
        Returns:
            Cleaned data in the same format as input
            
        Raises:
            TypeError: If data type is not supported
        """
        if isinstance(data, pd.DataFrame):
            return self._clean_dataframe(data)
        elif isinstance(data, pd.Series):
            return self._clean_series(data)
        elif isinstance(data, list):
            return self._clean_list(data)
        elif isinstance(data, dict):
            return self._clean_dict(data)
        elif isinstance(data, np.ndarray):
            return self._clean_array(data)
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean a pandas DataFrame while preserving missing values."""
        # Create a copy to avoid modifying original data
        df_copy = df.copy()
        
        # Store original dtypes
        for col in df_copy.columns:
            self._original_dtypes[col] = df_copy[col].dtype
        
        # Track missing value locations for each column
        for col in df_copy.columns:
            self._missing_value_map[col] = df_copy[col].isna()
        
        return df_copy
    
    def _clean_series(self, series: pd.Series) -> pd.Series:
        """Clean a pandas Series while preserving missing values."""
        # Create a copy to avoid modifying original data
        series_copy = series.copy()
        
        # Store original dtype
        self._original_dtypes['series'] = series_copy.dtype
        
        # Track missing value locations
        self._missing_value_map['series'] = series_copy.isna()
        
        return series_copy
    
    def _clean_list(self, data: List) -> List:
        """Clean a list while preserving missing values."""
        cleaned_list = []
        
        for i, item in enumerate(data):
            if item is None or (isinstance(item, float) and pd.isna(item)):
                cleaned_list.append(item)
            else:
                cleaned_list.append(item)
                
        return cleaned_list
    
    def _clean_dict(self, data: Dict) -> Dict:
        """Clean a dictionary while preserving missing values."""
        cleaned_dict = {}
        
        for key, value in data.items():
            if value is None or (isinstance(value, float) and pd.isna(value)):
                cleaned_dict[key] = value
            else:
                cleaned_dict[key] = value
                
        return cleaned_dict
    
    def _clean_array(self, arr: np.ndarray) -> np.ndarray:
        """Clean a numpy array while preserving missing values."""
        # Create a copy to avoid modifying original data
        arr_copy = arr.copy()
        
        # Track NaN locations if array contains floats
        if np.issubdtype(arr_copy.dtype, np.floating):
            self._missing_value_map['array'] = np.isnan(arr_copy)
        
        return arr_copy
    
    def handle_missing(self, data: Union[pd.DataFrame, pd.Series], 
                      method: str = 'preserve', 
                      fill_value: Any = None) -> Union[pd.DataFrame, pd.Series]:
        """
        Handle missing values in the data.
        
        Args:
            data: Input data (DataFrame or Series)
            method: Method to handle missing values ('preserve', 'fill', 'drop')
            fill_value: Value to use when method='fill'
            
        Returns:
            Data with missing values handled according to the specified method
            
        Raises:
            ValueError: If method is not recognized
        """
        if method == 'preserve':
            # Return data as-is, preserving all missing values
            return data.copy()
        elif method == 'fill':
            if fill_value is None:
                raise ValueError("fill_value must be provided when method='fill'")
            return data.fillna(fill_value)
        elif method == 'drop':
            if isinstance(data, pd.DataFrame):
                return data.dropna()
            else:
                return data.dropna()
        else:
            raise ValueError(f"Unknown method: {method}. Use 'preserve', 'fill', or 'drop'")
    
    def get_missing_value_report(self) -> Dict[str, Any]:
        """
        Generate a report of missing values in the cleaned data.
        
        Returns:
            Dictionary containing missing value statistics
        """
        report = {
            'total_missing_values': 0,
            'columns_with_missing': [],
            'missing_value_counts': {},
            'missing_value_percentages': {}
        }
        
        for key, mask in self._missing_value_map.items():
            if isinstance(mask, pd.Series):
                count = mask.sum()
                if count > 0:
                    report['columns_with_missing'].append(key)
                    report['missing_value_counts'][key] = int(count)
                    report['missing_value_percentages'][key] = float(count / len(mask) * 100)
                    report['total_missing_values'] += int(count)
            elif isinstance(mask, np.ndarray):
                count = mask.sum()
                if count > 0:
                    report['missing_value_counts'][key] = int(count)
                    report['total_missing_values'] += int(count)
        
        return report
    
    def restore_missing_values(self, data: Union[pd.DataFrame, pd.Series]) -> Union[pd.DataFrame, pd.Series]:
        """
        Restore original missing values to the data.
        
        Args:
            data: Data to restore missing values to
            
        Returns:
            Data with original missing values restored
        """
        if isinstance(data, pd.DataFrame):
            data_copy = data.copy()
            for col in data_copy.columns:
                if col in self._missing_value_map:
                    data_copy.loc[self._missing_value_map[col], col] = np.nan
            return data_copy
        elif isinstance(data, pd.Series):
            data_copy = data.copy()
            if 'series' in self._missing_value_map:
                data_copy.loc[self._missing_value_map['series']] = np.nan
            return data_copy
        else:
            return data
    
    def impute_missing(self, data: Union[pd.DataFrame, pd.Series], 
                      strategy: str = 'mean') -> Union[pd.DataFrame, pd.Series]:
        """
        Impute missing values while keeping track of original missing locations.
        
        Args:
            data: Data with missing values
            strategy: Imputation strategy ('mean', 'median', 'mode', 'forward', 'backward')
            
        Returns:
            Data with imputed values
            
        Raises:
            ValueError: If strategy is not recognized
        """
        data_copy = data.copy()
        
        if strategy == 'mean':
            if isinstance(data_copy, pd.DataFrame):
                for col in data_copy.select_dtypes(include=[np.number]).columns:
                    data_copy[col].fillna(data_copy[col].mean(), inplace=True)
            else:
                if pd.api.types.is_numeric_dtype(data_copy):
                    data_copy.fillna(data_copy.mean(), inplace=True)
        elif strategy == 'median':
            if isinstance(data_copy, pd.DataFrame):
                for col in data_copy.select_dtypes(include=[np.number]).columns:
                    data_copy[col].fillna(data_copy[col].median(), inplace=True)
            else:
                if pd.api.types.is_numeric_dtype(data_copy):
                    data_copy.fillna(data_copy.median(), inplace=True)
        elif strategy == 'mode':
            if isinstance(data_copy, pd.DataFrame):
                for col in data_copy.columns:
                    mode_val = data_copy[col].mode()
                    if len(mode_val) > 0:
                        data_copy[col].fillna(mode_val[0], inplace=True)
            else:
                mode_val = data_copy.mode()
                if len(mode_val) > 0:
                    data_copy.fillna(mode_val[0], inplace=True)
        elif strategy == 'forward':
            data_copy.fillna(method='ffill', inplace=True)
        elif strategy == 'backward':
            data_copy.fillna(method='bfill', inplace=True)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        return data_copy
```