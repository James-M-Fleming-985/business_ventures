```python
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import json


class TransformerService:
    """Service for transforming data with ISO 8601 UTC date handling."""
    
    def __init__(self):
        """Initialize the TransformerService."""
        self.transformations = []
    
    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform input data and add transformation metadata.
        
        Args:
            data: Input data dictionary to transform
            
        Returns:
            Transformed data with metadata
            
        Raises:
            ValueError: If input data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary")
        
        # Create transformation record
        transformation = {
            "input": data.copy(),
            "output": self._apply_transformation(data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.transformations.append(transformation)
        
        return transformation["output"]
    
    def _apply_transformation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply transformation rules to the data.
        
        Args:
            data: Input data to transform
            
        Returns:
            Transformed data
        """
        transformed = data.copy()
        
        # Add transformation metadata
        transformed["transformed_at"] = datetime.now(timezone.utc).isoformat()
        transformed["transformation_version"] = "1.0.0"
        
        # Apply specific transformations based on data content
        if "date" in transformed and transformed["date"]:
            transformed["date"] = self._ensure_iso8601_utc(transformed["date"])
        
        if "timestamp" in transformed and transformed["timestamp"]:
            transformed["timestamp"] = self._ensure_iso8601_utc(transformed["timestamp"])
        
        # Handle nested dates
        for key, value in transformed.items():
            if isinstance(value, dict):
                transformed[key] = self._apply_transformation(value)
            elif isinstance(value, list):
                transformed[key] = [
                    self._apply_transformation(item) if isinstance(item, dict) else item
                    for item in value
                ]
        
        return transformed
    
    def _ensure_iso8601_utc(self, date_string: str) -> str:
        """
        Ensure a date string is in ISO 8601 UTC format.
        
        Args:
            date_string: Date string to convert
            
        Returns:
            ISO 8601 UTC formatted date string
        """
        try:
            # Try parsing as ISO format
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except ValueError:
            # Try parsing common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f"
            ]
            
            dt = None
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_string, fmt)
                    break
                except ValueError:
                    continue
            
            if dt is None:
                # Return original if can't parse
                return date_string
        
        # Ensure UTC timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        
        return dt.isoformat()
    
    def get_transformation_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of all transformations.
        
        Returns:
            List of transformation records
        """
        return self.transformations.copy()
    
    def clear_history(self) -> None:
        """Clear the transformation history."""
        self.transformations.clear()
    
    def batch_transform(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform a batch of data items.
        
        Args:
            data_list: List of data dictionaries to transform
            
        Returns:
            List of transformed data
            
        Raises:
            ValueError: If input is not a list
        """
        if not isinstance(data_list, list):
            raise ValueError("Input must be a list")
        
        return [self.transform(data) for data in data_list]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get transformation statistics.
        
        Returns:
            Dictionary with transformation statistics
        """
        if not self.transformations:
            return {
                "total_transformations": 0,
                "first_transformation": None,
                "last_transformation": None,
                "average_processing_time": None
            }
        
        return {
            "total_transformations": len(self.transformations),
            "first_transformation": self.transformations[0]["timestamp"],
            "last_transformation": self.transformations[-1]["timestamp"],
            "average_processing_time": None  # Could be implemented with timing
        }


class DataValidator:
    """Validator for ensuring data meets requirements."""
    
    @staticmethod
    def validate_iso8601_utc(date_string: str) -> bool:
        """
        Validate that a string is in ISO 8601 UTC format.
        
        Args:
            date_string: Date string to validate
            
        Returns:
            True if valid ISO 8601 UTC format, False otherwise
        """
        try:
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            # Check if it's UTC
            return dt.tzinfo is not None and dt.utcoffset().total_seconds() == 0
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def validate_data_structure(data: Any, schema: Dict[str, Any]) -> bool:
        """
        Validate data against a schema.
        
        Args:
            data: Data to validate
            schema: Schema to validate against
            
        Returns:
            True if data matches schema, False otherwise
        """
        if not isinstance(data, dict) or not isinstance(schema, dict):
            return False
        
        for key, expected_type in schema.items():
            if key not in data:
                return False
            
            if expected_type == "iso8601_utc":
                if not DataValidator.validate_iso8601_utc(data[key]):
                    return False
            elif not isinstance(data[key], expected_type):
                return False
        
        return True


class TransformationPipeline:
    """Pipeline for chaining multiple transformations."""
    
    def __init__(self):
        """Initialize the transformation pipeline."""
        self.steps = []
    
    def add_step(self, step_func: callable, name: str = None) -> 'TransformationPipeline':
        """
        Add a transformation step to the pipeline.
        
        Args:
            step_func: Function to apply in this step
            name: Optional name for the step
            
        Returns:
            Self for method chaining
        """
        self.steps.append({
            "function": step_func,
            "name": name or step_func.__name__
        })
        return self
    
    def execute(self, data: Any) -> Any:
        """
        Execute the pipeline on input data.
        
        Args:
            data: Input data to process
            
        Returns:
            Transformed data after all steps
        """
        result = data
        for step in self.steps:
            result = step["function"](result)
        return result
    
    def clear(self) -> None:
        """Clear all steps from the pipeline."""
        self.steps.clear()


def ensure_dates_iso8601_utc(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure all date fields in data are in ISO 8601 UTC format.
    
    Args:
        data: Data dictionary potentially containing date fields
        
    Returns:
        Data with all dates converted to ISO 8601 UTC format
    """
    transformer = TransformerService()
    return transformer._apply_transformation(data)


def create_transformer() -> TransformerService:
    """
    Create and return a new TransformerService instance.
    
    Returns:
        New TransformerService instance
    """
    return TransformerService()
```