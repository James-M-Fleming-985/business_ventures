```python
"""Schema validation module for data validation before storage."""

import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class ValidationError:
    """Represents a single validation error."""
    field: str
    error: str
    value: Any = None


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    validated_data: Optional[Dict[str, Any]] = None


class SchemaValidator:
    """Validates data against predefined schemas."""
    
    def __init__(self):
        """Initialize the schema validator."""
        self._schemas: Dict[str, Dict[str, Any]] = {}
    
    def register_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """Register a schema for validation.
        
        Args:
            name: The name of the schema
            schema: The schema definition
        """
        self._schemas[name] = schema
    
    def validate(self, data: Dict[str, Any], schema_name: str) -> ValidationResult:
        """Validate data against a registered schema.
        
        Args:
            data: The data to validate
            schema_name: The name of the schema to validate against
            
        Returns:
            ValidationResult containing validation status and errors
        """
        if schema_name not in self._schemas:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(field='schema', error=f'Schema "{schema_name}" not found')]
            )
        
        schema = self._schemas[schema_name]
        errors = []
        validated_data = {}
        
        # Check required fields
        required_fields = schema.get('required', [])
        for field_name in required_fields:
            if field_name not in data:
                errors.append(ValidationError(
                    field=field_name,
                    error=f'Required field "{field_name}" is missing'
                ))
        
        # Validate each field
        properties = schema.get('properties', {})
        for field_name, field_value in data.items():
            if field_name in properties:
                field_schema = properties[field_name]
                field_errors = self._validate_field(field_name, field_value, field_schema)
                errors.extend(field_errors)
                if not field_errors:
                    validated_data[field_name] = field_value
            else:
                # Field not in schema
                errors.append(ValidationError(
                    field=field_name,
                    error=f'Field "{field_name}" not allowed in schema',
                    value=field_value
                ))
        
        # Add default values for missing optional fields
        for field_name, field_schema in properties.items():
            if field_name not in data and field_name not in required_fields:
                if 'default' in field_schema:
                    validated_data[field_name] = field_schema['default']
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            validated_data=validated_data if len(errors) == 0 else None
        )
    
    def _validate_field(self, field_name: str, value: Any, field_schema: Dict[str, Any]) -> List[ValidationError]:
        """Validate a single field against its schema.
        
        Args:
            field_name: The name of the field
            value: The value to validate
            field_schema: The schema for this field
            
        Returns:
            List of validation errors for this field
        """
        errors = []
        
        # Type validation
        if 'type' in field_schema:
            expected_type = field_schema['type']
            if not self._check_type(value, expected_type):
                errors.append(ValidationError(
                    field=field_name,
                    error=f'Expected type "{expected_type}", got "{type(value).__name__}"',
                    value=value
                ))
                return errors  # No point in further validation if type is wrong
        
        # String validation
        if field_schema.get('type') == 'string':
            if 'minLength' in field_schema and len(value) < field_schema['minLength']:
                errors.append(ValidationError(
                    field=field_name,
                    error=f'String length must be at least {field_schema["minLength"]}',
                    value=value
                ))
            if 'maxLength' in field_schema and len(value) > field_schema['maxLength']:
                errors.append(ValidationError(
                    field=field_name,
                    error=f'String length must not exceed {field_schema["maxLength"]}',
                    value=value
                ))
            if 'pattern' in field_schema:
                import re
                if not re.match(field_schema['pattern'], value):
                    errors.append(ValidationError(
                        field=field_name,
                        error=f'String does not match pattern "{field_schema["pattern"]}"',
                        value=value
                    ))
        
        # Number validation
        if field_schema.get('type') in ['integer', 'number']:
            if 'minimum' in field_schema and value < field_schema['minimum']:
                errors.append(ValidationError(
                    field=field_name,
                    error=f'Value must be at least {field_schema["minimum"]}',
                    value=value
                ))
            if 'maximum' in field_schema and value > field_schema['maximum']:
                errors.append(ValidationError(
                    field=field_name,
                    error=f'Value must not exceed {field_schema["maximum"]}',
                    value=value
                ))
        
        # Enum validation
        if 'enum' in field_schema and value not in field_schema['enum']:
            errors.append(ValidationError(
                field=field_name,
                error=f'Value must be one of {field_schema["enum"]}',
                value=value
            ))
        
        return errors
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if a value matches the expected type.
        
        Args:
            value: The value to check
            expected_type: The expected type as a string
            
        Returns:
            True if the value matches the expected type
        """
        type_mapping = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        if expected_type not in type_mapping:
            return False
        
        expected_python_type = type_mapping[expected_type]
        if expected_type == 'integer' and isinstance(value, bool):
            return False  # bool is a subclass of int in Python
        
        return isinstance(value, expected_python_type)


class DataStorage:
    """Handles data storage with schema validation."""
    
    def __init__(self, validator: SchemaValidator):
        """Initialize the data storage.
        
        Args:
            validator: The schema validator to use
        """
        self._validator = validator
        self._storage: Dict[str, List[Dict[str, Any]]] = {}
    
    def store(self, collection: str, data: Dict[str, Any], schema_name: str) -> Union[Dict[str, Any], ValidationResult]:
        """Store data after validating against a schema.
        
        Args:
            collection: The collection to store data in
            data: The data to store
            schema_name: The schema to validate against
            
        Returns:
            The stored data if validation passes, ValidationResult with errors otherwise
        """
        validation_result = self._validator.validate(data, schema_name)
        
        if not validation_result.is_valid:
            return validation_result
        
        if collection not in self._storage:
            self._storage[collection] = []
        
        self._storage[collection].append(validation_result.validated_data)
        return validation_result.validated_data
    
    def get_all(self, collection: str) -> List[Dict[str, Any]]:
        """Get all data from a collection.
        
        Args:
            collection: The collection to retrieve data from
            
        Returns:
            List of all data in the collection
        """
        return self._storage.get(collection, [])
    
    def clear(self, collection: str) -> None:
        """Clear all data from a collection.
        
        Args:
            collection: The collection to clear
        """
        if collection in self._storage:
            del self._storage[collection]


# Example usage and convenience functions
def create_validator_with_schema(schema_name: str, schema: Dict[str, Any]) -> SchemaValidator:
    """Create a validator with a pre-registered schema.
    
    Args:
        schema_name: The name of the schema
        schema: The schema definition
        
    Returns:
        SchemaValidator with the schema registered
    """
    validator = SchemaValidator()
    validator.register_schema(schema_name, schema)
    return validator


def validate_and_store(storage: DataStorage, collection: str, data: Dict[str, Any], schema_name: str) -> Union[Dict[str, Any], List[str]]:
    """Validate and store data, returning stored data or error messages.
    
    Args:
        storage: The data storage instance
        collection: The collection to store in
        data: The data to validate and store
        schema_name: The schema to validate against
        
    Returns:
        Stored data dict if successful, list of error messages if validation fails
    """
    result = storage.store(collection, data, schema_name)
    
    if isinstance(result, ValidationResult):
        return [f"{err.field}: {err.error}" for err in result.errors]
    
    return result
```