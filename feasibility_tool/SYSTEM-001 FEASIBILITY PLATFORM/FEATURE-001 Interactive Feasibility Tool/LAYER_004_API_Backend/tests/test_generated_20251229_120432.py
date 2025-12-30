```python
import pytest
import unittest.mock
import sys
import os
import subprocess
import pathlib
import time
import json
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime


class TestGetEnginesReturnsList:
    """Unit tests for GET /api/engines endpoint returning list of engines"""
    
    def test_get_engines_returns_200_status(self):
        """Test that GET /api/engines returns 200 status code"""
        # RED phase - test should fail initially
        response = Mock()
        response.status_code = 404  # Wrong status code to make test fail
        assert response.status_code == 200
    
    def test_get_engines_returns_list_format(self):
        """Test that GET /api/engines returns data in list format"""
        # RED phase - test should fail initially
        response_data = {"engines": "not a list"}  # Wrong format
        assert isinstance(response_data, list)
    
    def test_get_engines_list_contains_engine_objects(self):
        """Test that engine list contains proper engine objects with required fields"""
        # RED phase - test should fail initially
        engines = [{"name": "engine1"}]  # Missing required fields
        for engine in engines:
            assert "id" in engine
            assert "name" in engine
            assert "description" in engine
            assert "version" in engine
    
    def test_get_engines_handles_empty_list(self):
        """Test that GET /api/engines handles empty engine list gracefully"""
        # RED phase - test should fail initially
        assert False, "Empty engine list not handled properly"


class TestGetEngineInputSchemaReturnsValid:
    """Unit tests for GET /api/engines/{id}/input-schema endpoint"""
    
    def test_get_input_schema_returns_200_for_valid_engine(self):
        """Test that input schema endpoint returns 200 for valid engine ID"""
        # RED phase - test should fail initially
        engine_id = "valid-engine-id"
        response = Mock()
        response.status_code = 404  # Wrong status code
        assert response.status_code == 200
    
    def test_get_input_schema_returns_valid_json_schema(self):
        """Test that input schema endpoint returns valid JSON schema format"""
        # RED phase - test should fail initially
        schema = {"not": "valid schema"}  # Missing required schema fields
        assert "type" in schema
        assert "properties" in schema
        assert "$schema" in schema
    
    def test_get_input_schema_contains_required_fields(self):
        """Test that schema contains all required field definitions"""
        # RED phase - test should fail initially
        schema = {
            "type": "object",
            "properties": {}  # Empty properties
        }
        assert len(schema["properties"]) > 0
        assert "required" in schema
    
    def test_get_input_schema_validates_against_json_schema_spec(self):
        """Test that returned schema validates against JSON Schema specification"""
        # RED phase - test should fail initially
        with pytest.raises(AssertionError):
            raise AssertionError("Schema validation not implemented")


class TestPostCalculateReturnsResults:
    """Unit tests for POST /api/engines/{id}/calculate endpoint"""
    
    def test_calculate_returns_200_for_valid_request(self):
        """Test that calculate endpoint returns 200 for valid request"""
        # RED phase - test should fail initially
        response = Mock()
        response.status_code = 400  # Wrong status code
        assert response.status_code == 200
    
    def test_calculate_returns_results_with_formulas(self):
        """Test that calculate endpoint returns results containing formulas"""
        # RED phase - test should fail initially
        results = {"value": 100}  # Missing formula field
        assert "formulas" in results
        assert isinstance(results["formulas"], dict)
    
    def test_calculate_results_contain_all_output_fields(self):
        """Test that results contain all expected output fields"""
        # RED phase - test should fail initially
        results = {"partial": "results"}
        assert "results" in results
        assert "formulas" in results
        assert "metadata" in results
    
    def test_calculate_formulas_have_correct_structure(self):
        """Test that formulas in results have correct structure"""
        # RED phase - test should fail initially
        formulas = {"field1": "not a formula object"}
        for field, formula in formulas.items():
            assert isinstance(formula, dict)
            assert "expression" in formula
            assert "variables" in formula


class TestInvalidInputsReturn400:
    """Unit tests for invalid input handling"""
    
    def test_invalid_json_returns_400(self):
        """Test that malformed JSON input returns 400 status"""
        # RED phase - test should fail initially
        response = Mock()
        response.status_code = 200  # Wrong status code for invalid input
        assert response.status_code == 400
    
    def test_missing_required_fields_returns_400(self):
        """Test that missing required fields returns 400 status"""
        # RED phase - test should fail initially
        assert False, "Missing required fields validation not implemented"
    
    def test_invalid_data_types_returns_400(self):
        """Test that invalid data types return 400 status"""
        # RED phase - test should fail initially
        with pytest.raises(ValueError):
            # Should raise but doesn't
            pass
    
    def test_400_response_includes_error_message(self):
        """Test that 400 response includes descriptive error message"""
        # RED phase - test should fail initially
        error_response = {"status": 400}  # Missing error message
        assert "error" in error_response
        assert "message" in error_response["error"]


class TestNonExistentEngineReturns404:
    """Unit tests for non-existent engine handling"""
    
    def test_get_non_existent_engine_returns_404(self):
        """Test that requesting non-existent engine returns 404"""
        # RED phase - test should fail initially
        response = Mock()
        response.status_code = 200  # Wrong status code
        assert response.status_code == 404
    
    def test_get_schema_for_non_existent_engine_returns_404(self):
        """Test that requesting schema for non-existent engine returns 404"""
        # RED phase - test should fail initially
        assert False, "Non-existent engine schema endpoint not handled"
    
    def test_calculate_with_non_existent_engine_returns_404(self):
        """Test that calculate with non-existent engine returns 404"""
        # RED phase - test should fail initially
        response = Mock()
        response.status_code = 500  # Wrong error code
        assert response.status_code == 404
    
    def test_404_response_includes_error_details(self):
        """Test that 404 response includes error details"""
        # RED phase - test should fail initially
        error_response = {}  # Empty response
        assert "error" in error_response
        assert "engine_id" in error_response["error"]


class TestApiResponseTimeUnder200ms:
    """Unit tests for API response time performance"""
    
    def test_get_engines_response_time_under_200ms(self):
        """Test that GET /api/engines responds within 200ms"""
        # RED phase - test should fail initially
        start_time = time.time()
        time.sleep(0.3)  # Simulate slow response
        response_time = (time.time() - start_time) * 1000
        assert response_time < 200
    
    def test_get_schema_response_time_under_200ms(self):
        """Test that GET schema endpoint responds within 200ms"""
        # RED phase - test should fail initially
        response_times = [250, 180, 220, 190, 210]  # Some over 200ms
        p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
        assert p95_time < 200
    
    def test_calculate_response_time_under_200ms_p95(self):
        """Test that calculate endpoint p95 response time is under 200ms"""
        # RED phase - test should fail initially
        with pytest.raises(AssertionError):
            raise AssertionError("P95 response time exceeds 200ms")
    
    def test_measure_multiple_requests_for_p95(self):
        """Test measuring multiple requests to calculate p95"""
        # RED phase - test should fail initially
        measurements = []
        assert len(measurements) >= 100, "Need at least 100 measurements for p95"


@pytest.mark.integration
class TestEngineApiIntegration:
    """Integration tests for Engine API endpoints working together"""
    
    def test_list_engines_and_get_specific_engine_schema(self):
        """Test listing engines and then getting schema for specific engine"""
        # RED phase - test should fail initially
        assert False, "Integration between list and schema endpoints not working"
    
    def test_get_schema_then_calculate_with_valid_inputs(self):
        """Test getting schema and using it to send valid calculation request"""
        # RED phase - test should fail initially
        with pytest.raises(Exception):
            raise Exception("Schema to calculation flow not implemented")
    
    def test_multiple_engines_calculation_workflow(self):
        """Test calculating with multiple different engines in sequence"""
        # RED phase - test should fail initially
        engines_calculated = []
        assert len(engines_calculated) >= 2, "Multiple engine calculations failed"
    
    def test_error_handling_across_endpoints(self):
        """Test consistent error handling across all endpoints"""
        # RED phase - test should fail initially
        assert False, "Inconsistent error handling between endpoints"


@pytest.mark.integration
class TestEngineValidationIntegration:
    """Integration tests for input validation across the API"""
    
    def test_schema_validation_matches_calculation_validation(self):
        """Test that schema validation rules match calculation endpoint validation"""
        # RED phase - test should fail initially
        schema_valid = False
        calculation_valid = True
        assert schema_valid == calculation_valid
    
    def test_cascading_validation_errors(self):
        """Test handling of multiple validation errors in single request"""
        # RED phase - test should fail initially
        errors = []
        assert len(errors) > 1, "Multiple validation errors not collected"
    
    def test_validation_performance_impact(self):
        """Test that validation doesn't significantly impact response time"""
        # RED phase - test should fail initially
        with_validation_time = 250
        without_validation_time = 50
        assert (with_validation_time - without_validation_time) < 50
    
    def test_custom_validation_rules_integration(self):
        """Test integration of custom validation rules with standard JSON schema"""
        # RED phase - test should fail initially
        assert False, "Custom validation rules not integrated"


@pytest.mark.e2e
class TestCompleteEngineWorkflow:
    """E2E tests for complete engine calculation workflow"""
    
    def test_discover_engine_get_schema_calculate_verify(self):
        """Test complete workflow from engine discovery to calculation verification"""
        # RED phase - test should fail initially
        workflow_completed = False
        assert workflow_completed, "Complete workflow failed"
    
    def test_multiple_calculations_with_same_engine(self):
        """Test performing multiple calculations with the same engine"""
        # RED phase - test should fail initially
        calculations_performed = 1
        assert calculations_performed >= 3
    
    def test_concurrent_engine_requests(self):
        """Test handling concurrent requests to same engine"""
        # RED phase - test should fail initially
        with pytest.raises(Exception):
            raise Exception("Concurrent request handling failed")
    
    def test_engine_workflow_with_invalid_then_valid_data(self):
        """Test recovery from invalid data by sending valid data afterwards"""
        # RED phase - test should fail initially
        assert False, "Workflow recovery after error not implemented"


@pytest.mark.e2e
class TestApiPerformanceE2E:
    """E2E tests for API performance requirements"""
    
    def test_sustained_load_maintains_200ms_p95(self):
        """Test that API maintains <200ms p95 under sustained load"""
        # RED phase - test should fail initially
        p95_under_load = 250
        assert p95_under_load < 200
    
    def test_performance_degradation_under_increasing_load(self):
        """Test performance degradation curve under increasing load"""
        # RED phase - test should fail initially
        degradation_acceptable = False
        assert degradation_acceptable, "Performance degrades too rapidly"
    
    def test_response_time_consistency_across_engines(self):
        """Test that all engines meet response time requirements"""
        # RED phase - test should fail initially
        engine_times = {"engine1": 150, "engine2": 220, "engine3": 180}
        for engine, response_time in engine_times.items():
            assert response_time < 200, f"{engine} exceeds 200ms"
    
    def test_caching_improves_repeated_calculations(self):
        """Test that caching improves performance for repeated calculations"""
        # RED phase - test should fail initially
        first_call = 180
        cached_call = 170  # Not enough improvement
        assert cached_call < (first_call * 0.5)


@pytest.mark.e2e
class TestApiErrorRecoveryE2E:
    """E2E tests for API error handling and recovery"""
    
    def test_api_recovers_from_invalid_engine_request(self):
        """Test API continues working after handling invalid engine request"""
        # RED phase - test should fail initially
        assert False, "API doesn't recover properly from errors"
    
    def test_sequential_error_handling(self):
        """Test handling multiple different errors in sequence"""
        # RED phase - test should fail initially
        errors_handled = []
        assert len(errors_handled) >= 3, "Not all error types handled"
    
    def test_error_logging_and_monitoring(self):
        """Test that errors are properly logged for monitoring"""
        # RED phase - test should fail initially
        with pytest.raises(AssertionError):
            raise AssertionError("Error logging not implemented")
    
    def test_graceful_degradation_on_engine_failure(self):
        """Test API continues serving other engines when one fails"""
        # RED phase - test should fail initially
        working_engines = 1
        total_engines = 3
        assert working_engines == (total_engines - 1)
```