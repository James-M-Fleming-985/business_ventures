"""Data Transformer Service - Layer: Transformation

Transforms data between different formats.
"""

from typing import Any, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Transformer:
    """Transforms data formats and structures."""
    
    def __init__(self):
        """Initialize transformer."""
        logger.info("Transformer initialized")
    
    async def to_snake_case(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert keys to snake_case.
        
        Args:
            data: Input data with camelCase or other formats
            
        Returns:
            Data with snake_case keys
        """
        import re
        result = {}
        for key, value in data.items():
            snake_key = re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower()
            result[snake_key] = value
        return result
    
    async def add_timestamps(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add processing timestamps.
        
        Args:
            data: Input data
            
        Returns:
            Data with added timestamp fields
        """
        result = data.copy()
        result['processed_at'] = datetime.utcnow().isoformat()
        return result
    
    async def flatten(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested dictionaries.
        
        Args:
            data: Nested dictionary
            
        Returns:
            Flattened dictionary with dot notation keys
        """
        result = {}
        
        def _flatten(obj: Dict[str, Any], prefix: str = ''):
            for key, value in obj.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    _flatten(value, new_key)
                else:
                    result[new_key] = value
        
        _flatten(data)
        return result
    
    async def transform(
        self, 
        data: Dict[str, Any],
        snake_case: bool = True,
        add_ts: bool = True,
        flatten: bool = False
    ) -> Dict[str, Any]:
        """Apply transformation pipeline.
        
        Args:
            data: Input data
            snake_case: Convert to snake_case
            add_ts: Add timestamp
            flatten: Flatten nested structures
            
        Returns:
            Transformed data
        """
        result = data.copy()
        
        if flatten:
            result = await self.flatten(result)
        
        if snake_case:
            result = await self.to_snake_case(result)
        
        if add_ts:
            result = await self.add_timestamps(result)
        
        return result
