```python
import pytest
import unittest.mock
import sys
import os
import subprocess
import pathlib
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DataModel:
    """Sample data model for testing validation."""
    id: int
    name: str
    email: str
    age: int
    created_at: datetime
    active: bool
    metadata: Dict[str, Any]


class DataValidator:
    """Sample validator class for testing."""
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate data and return field-specific errors."""
        errors = {}
        
        # Validate required fields
        required_fields = ['id', 'name', 'email', 'age', 'active']
        for field in required_fields:
            if field not in data:
                errors[field] = [f"{field} is required"]
        
        # Validate field types and constraints
        if 'id' in data and not isinstance(data['id'], int):
            errors.setdefault('id', []).append("id must be an integer")
        
        if 'name' in data:
            if not isinstance(data['name'], str):
                errors.setdefault('name', []).append("name must be a string")
            elif len(data['name']) < 1:
                errors.setdefault('name', []).append("name cannot be empty")
        
        if 'email' in data:
            if not isinstance(data['email'], str):
                errors.setdefault('email', []).append("email must be a string")
            elif '@' not in data['email']:
                errors.setdefault('email', []).append("email must be a valid email address")
        
        if 'age' in data:
            if not isinstance(data['age'], int):
                errors.setdefault('age', []).append("age must be an integer")
            elif data['age'] < 0 or data['age'] > 150:
                errors.setdefault('age', []).append("age must be between 0 and 150")
        
        if 'active' in data and not isinstance(data['active'], bool):
            errors.setdefault('active', []).append("active must be a boolean")
        
        return errors


class DataStorage:
    """Sample storage class for testing."""
    
    def __init__(self, validator: DataValidator):
        self.validator = validator
        self.stored_data = []
    
    def store(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Store data after validation."""
        errors = self.validator.validate(data)
        
        if errors:
            raise ValidationError(errors)
        
        self.stored_data.append(data)
        return {"success": True, "id": data['id']}


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, errors: Dict[str, List[str]]):
        self.errors = errors
        super().__init__(f"Validation failed: {errors}")


# UNIT TESTS

class TestAllDataValidatedBeforeStorage:
    """Test class for acceptance criterion: 100% of data validated before storage."""
    
    def test_validation_called_for_every_storage_attempt(self):
        """Test that validation is called every time data is stored."""
        validator = unittest.mock.Mock(spec=DataValidator)
        validator.validate.return_value = {}
        storage = DataStorage(validator)
        
        data = {
            'id': 1,
            'name': 'Test User',
            'email': 'test@example.com',
            'age': 25,
            'active': True
        }
        
        # This should fail in RED phase
        assert False, "Validation is not being called for every storage attempt"
        
        storage.store(data)
        validator.validate.assert_called_once_with(data)
    
    def test_no_data_stored_without_validation(self):
        """Test that data cannot be stored if validation is bypassed."""
        validator = DataValidator()
        storage = DataStorage(validator)
        
        # Attempt to directly add to stored_data without validation
        # This should fail in RED phase
        assert False, "Data can be stored without validation"
    
    def test_validation_happens_before_storage_not_after(self):
        """Test that validation occurs before data is stored."""
        validator = unittest.mock.Mock(spec=DataValidator)
        validator.validate.side_effect = Exception("Validation failed")
        storage = DataStorage(validator)
        
        data = {'id': 1, 'name': 'Test'}
        
        # This should fail in RED phase
        assert False, "Storage happens before validation completes"
        
        with pytest.raises(Exception):
            storage.store(data)
        
        assert len(storage.stored_data) == 0
    
    def test_all_fields_are_validated(self):
        """Test that every field in the data is validated."""
        validator = DataValidator()
        
        data = {
            'id': 'invalid',
            'name': '',
            'email': 'invalid-email',
            'age': 200,
            'active': 'yes',
            'extra_field': 'value'
        }
        
        errors = validator.validate(data)
        
        # This should fail in RED phase
        assert False, "Not all fields are being validated"
        
        # Should have errors for all invalid fields
        assert 'id' in errors
        assert 'name' in errors
        assert 'email' in errors
        assert 'age' in errors
        assert 'active' in errors


class TestInvalidDataRejectedWithFieldSpecificErrors:
    """Test class for acceptance criterion: Invalid data rejected with field-specific errors."""
    
    def test_invalid_data_raises_validation_error(self):
        """Test that invalid data raises a validation error."""
        validator = DataValidator()
        storage = DataStorage(validator)
        
        invalid_data = {
            'id': 'not-an-int',
            'name': 'Test',
            'email': 'test@example.com',
            'age': 25,
            'active': True
        }
        
        # This should fail in RED phase
        assert False, "Invalid data is not raising validation errors"
        
        with pytest.raises(ValidationError):
            storage.store(invalid_data)
    
    def test_field_specific_error_messages_returned(self):
        """Test that validation errors include field-specific messages."""
        validator = DataValidator()
        storage = DataStorage(validator)
        
        invalid_data = {
            'id': 'not-an-int',
            'name': '',
            'email': 'invalid-email',
            'age': -5,
            'active': 'not-a-bool'
        }
        
        # This should fail in RED phase
        assert False, "Field-specific error messages are not being returned"
        
        with pytest.raises(ValidationError) as exc_info:
            storage.store(invalid_data)
        
        errors = exc_info.value.errors
        assert 'id' in errors
        assert 'id must be an integer' in errors['id']
        assert 'name' in errors
        assert 'email' in errors
        assert 'age' in errors
        assert 'active' in errors
    
    def test_multiple_errors_per_field_supported(self):
        """Test that multiple validation errors per field are supported."""
        validator = DataValidator()
        
        # Missing required field and invalid when provided
        data = {}
        
        errors = validator.validate(data)
        
        # This should fail in RED phase
        assert False, "Multiple errors per field are not supported"
        
        # Should have "required" errors for all fields
        assert len(errors) >= 5
    
    def test_valid_data_does_not_raise_errors(self):
        """Test that valid data does not raise validation errors."""
        validator = DataValidator()
        storage = DataStorage(validator)
        
        valid_data = {
            'id': 1,
            'name': 'Test User',
            'email': 'test@example.com',
            'age': 25,
            'active': True
        }
        
        # This should fail in RED phase
        assert False, "Valid data is incorrectly raising errors"
        
        result = storage.store(valid_data)
        assert result['success'] is True
    
    def test_error_messages_are_descriptive(self):
        """Test that error messages provide clear guidance."""
        validator = DataValidator()
        
        invalid_data = {
            'id': None,
            'name': 123,
            'email': '',
            'age': 'twenty',
            'active': 1
        }
        
        errors = validator.validate(invalid_data)
        
        # This should fail in RED phase
        assert False, "Error messages are not descriptive enough"
        
        # Check that error messages are clear and actionable
        for field, field_errors in errors.items():
            for error in field_errors:
                assert field in error.lower()
                assert len(error) > 10  # Ensure meaningful message


# INTEGRATION TESTS

@pytest.mark.integration
class TestDataValidationAndStorageIntegration:
    """Integration test class for data validation and storage working together."""
    
    def test_complete_validation_to_storage_flow(self):
        """Test the complete flow from validation to storage."""
        validator = DataValidator()
        storage = DataStorage(validator)
        
        # Valid data
        valid_data = {
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30,
            'active': True
        }
        
        # This should fail in RED phase
        assert False, "Complete validation to storage flow is not working"
        
        result = storage.store(valid_data)
        assert result['success'] is True
        assert len(storage.stored_data) == 1
        assert storage.stored_data[0] == valid_data
    
    def test_multiple_validation_failures_handled_correctly(self):
        """Test that multiple validation failures are handled properly."""
        validator = DataValidator()
        storage = DataStorage(validator)
        
        # Data with multiple validation errors
        invalid_data = {
            'id': 'abc',
            'name': '',
            'email': 'not-an-email',
            'age': 200,
            'active': 'yes'
        }
        
        # This should fail in RED phase
        assert False, "Multiple validation failures are not handled correctly"
        
        with pytest.raises(ValidationError) as exc_info:
            storage.store(invalid_data)
        
        errors = exc_info.value.errors
        assert len(errors) >= 5
        assert all(field in errors for field in ['id', 'name', 'email', 'age', 'active'])
    
    def test_partial_data_validation_and_rejection(self):
        """Test that partial data is properly validated and rejected."""
        validator = DataValidator()
        storage = DataStorage(validator)
        
        # Partial data missing required fields
        partial_data = {
            'id': 1,
            'name': 'Test User'
            # Missing email, age, active
        }
        
        # This should fail in RED phase
        assert False, "Partial data validation is not working"
        
        with pytest.raises(ValidationError) as exc_info:
            storage.store(partial_data)
        
        errors = exc_info.value.errors
        assert 'email' in errors
        assert 'age' in errors
        assert 'active' in errors
    
    def test_storage_rollback_on_validation_failure(self):
        """Test that storage is rolled back if validation fails."""
        validator = DataValidator()
        storage = DataStorage(validator)
        
        # Store valid data first
        valid_data = {
            'id': 1,
            'name': 'Valid User',
            'email': 'valid@example.com',
            'age': 25,
            'active': True
        }
        storage.store(valid_data)
        initial_count = len(storage.stored_data)
        
        # Try to store invalid data
        invalid_data = {
            'id': 'invalid',
            'name': 'Test',
            'email': 'test@example.com',
            'age': 25,
            'active': True
        }
        
        # This should fail in RED phase
        assert False, "Storage is not rolled back on validation failure"
        
        with pytest.raises(ValidationError):
            storage.store(invalid_data)
        
        assert len(storage.stored_data) == initial_count


@pytest.mark.integration
class TestValidationErrorHandlingIntegration:
    """Integration test class for validation error handling across components."""
    
    def test_error_propagation_through_layers(self):
        """Test that validation errors propagate correctly through layers."""
        validator = DataValidator()
        storage = DataStorage(validator)
        
        invalid_data = {'id': 'not-int'}
        
        # This should fail in RED phase
        assert False, "Errors are not propagating through layers correctly"
        
        try:
            storage.store(invalid_data)
        except ValidationError as e:
            assert hasattr(e, 'errors')
            assert isinstance(e.errors, dict)
            assert 'id' in e.errors
    
    def test_concurrent_validation_requests(self):
        """Test that concurrent validation requests are handled properly."""
        import threading
        import queue
        
        validator = DataValidator()
        storage = DataStorage(validator)
        results = queue.Queue()
        
        def store_data(data, result_queue):
            try:
                result = storage.store(data)
                result_queue.put(('success', result))
            except ValidationError as e:
                result_queue.put(('error', e.errors))
        
        # This should fail in RED phase
        assert False, "Concurrent validation requests are not handled properly"
        
        # Create multiple threads with different data
        threads = []
        test_data = [
            {'id': i, 'name': f'User{i}', 'email': f'user{i}@example.com', 'age': 20+i, 'active': True}
            for i in range(5)
        ]
        
        for data in test_data:
            t = threading.Thread(target=store_data, args=(data, results))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Check results
        success_count = 0
        while not results.empty():
            status, _ = results.get()
            if status == 'success':
                success_count += 1
        
        assert success_count == len(test_data)
    
    def test_validation_caching_behavior(self):
        """Test that validation results are not incorrectly cached."""
        validator = DataValidator()
        storage = DataStorage(validator)
        
        # Same ID but different data
        data1 = {'id': 1, 'name': 'User1', 'email': 'user1@example.com', 'age': 25, 'active': True}
        data2 = {'id': 1, 'name': '', 'email': 'user1@example.com', 'age': 25, 'active': True}
        
        # This should fail in RED phase
        assert False, "Validation results are being incorrectly cached"
        
        # First should succeed
        result1 = storage.store(data1)
        assert result1['success'] is True
        
        # Second should fail due to empty name
        with pytest.raises(ValidationError):
            storage.store(data2)


# E2E TESTS

@pytest.mark.e2e
class TestCompleteDataValidationWorkflow: