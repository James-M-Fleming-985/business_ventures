"""Data Cleaner Service - Layer: Data Cleaning

Removes anomalies, nulls, and normalizes data.
"""

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """Cleans and normalizes incoming data."""
    
    def __init__(self):
        """Initialize data cleaner."""
        logger.info("DataCleaner initialized")
    
    async def remove_nulls(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove null/None values from data.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Cleaned data without null values
        """
        return {k: v for k, v in data.items() if v is not None}
    
    async def remove_duplicates(
        self, 
        data_list: List[Dict[str, Any]], 
        key: str
    ) -> List[Dict[str, Any]]:
        """Remove duplicate records based on key.
        
        Args:
            data_list: List of data records
            key: Field name to use for deduplication
            
        Returns:
            Deduplicated list
        """
        seen = set()
        result = []
        for item in data_list:
            if item.get(key) not in seen:
                seen.add(item.get(key))
                result.append(item)
        return result
    
    async def normalize_strings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize string values (trim, lowercase, etc).
        
        Args:
            data: Input data
            
        Returns:
            Data with normalized strings
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = value.strip().lower()
            else:
                result[key] = value
        return result
    
    async def clean(
        self, 
        data: Dict[str, Any], 
        remove_nulls: bool = True,
        normalize: bool = True
    ) -> Dict[str, Any]:
        """Apply all cleaning operations.
        
        Args:
            data: Input data
            remove_nulls: Whether to remove null values
            normalize: Whether to normalize strings
            
        Returns:
            Fully cleaned data
        """
        result = data.copy()
        
        if remove_nulls:
            result = await self.remove_nulls(result)
        
        if normalize:
            result = await self.normalize_strings(result)
        
        logger.debug(f"Cleaned data: {len(data)} -> {len(result)} fields")
        return result
