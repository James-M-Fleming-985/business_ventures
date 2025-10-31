"""
Integration tests for CA-001 CA-002 System Integration
Tests the integration between all layers of the feature
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
import asyncio
from typing import Dict, List, Any

# Mock imports for the layers
from ca001_data_connector import CA001DataConnector, ConnectionError, DataFetchError
from data_format_orchestrator import DataFormatOrchestrator, FormatError, ValidationError
from feature_integration_controller import FeatureIntegrationController, IntegrationError
from system_integration_api import SystemIntegrationAPI, APIError, AuthenticationError


class TestCA001CA002Integration:
    """Integration tests for CA-001 CA-002 System Integration"""

    @pytest.fixture
    def ca001_connector(self):
        """Fixture for CA-001 Data Connector"""
        connector = Mock(spec=CA001DataConnector)
        connector.is_connected = False
        connector.connection_params = {
            "host": "test.ca001.local",
            "port": 5432,
            "timeout": 30
        }
        return connector

    @pytest.fixture
    def format_orchestrator(self):
        """Fixture for Data Format Orchestrator"""
        orchestrator = Mock(spec=DataFormatOrchestrator)
        orchestrator.supported_formats = ["JSON", "XML", "CSV"]
        orchestrator.validation_rules = {
            "required_fields": ["id", "timestamp", "data"],
            "data_types": {"id": str, "timestamp": datetime, "data": dict}
        }
        return orchestrator

    @pytest.fixture
    def integration_controller(self):
        """Fixture for Feature Integration Controller"""
        controller = Mock(spec=FeatureIntegrationController)
        controller.integration_status = "initialized"
        controller.error_handlers = {}
        return controller

    @pytest.fixture
    def system_api(self):
        """Fixture for System Integration API"""
        api = Mock(spec=SystemIntegrationAPI)
        api.base_url = "https://api.system.local/v1"
        api.auth_token = None
        api.rate_limit = 100
        return api

    @pytest.fixture
    def feature_integration(self, ca001_connector, format_orchestrator, 
                           integration_controller, system_api):
        """Fixture for the complete feature integration"""
        class FeatureIntegration:
            def __init__(self):
                self.ca001_connector = ca001_connector
                self.format_orchestrator = format_orchestrator
                self.integration_controller = integration_controller
                self.system_api = system_api
                
            async def process_data_flow(self, request_data):
                """Process data through all layers"""
                # Layer 1: Connect and fetch data
                if not self.ca001_connector.is_connected:
                    self.ca001_connector.connect()
                    
                raw_data = self.ca001_connector.fetch_data(request_data.get("query"))
                
                # Layer 2: Format and validate data
                formatted_data = self.format_orchestrator.format_data(
                    raw_data, 
                    request_data.get("format", "JSON")
                )
                
                # Layer 3: Process through integration controller
                processed_data = self.integration_controller.process(formatted_data)
                
                # Layer 4: Send through API
                response = self.system_api.send_data(processed_data)
                
                return response
                
        return FeatureIntegration()

    @pytest.mark.asyncio
    async def test_successful_end_to_end_data_flow(self, feature_integration):
        """Test 1: Successful end-to-end data flow through all layers"""
        # Setup
        test_query = {"query": "SELECT * FROM ca001_data WHERE status='active'"}
        raw_test_data = [
            {"id": "001", "timestamp": "2024-01-15T10:30:00", "data": {"value": 100}},
            {"id": "002", "timestamp": "2024-01-15T10:31:00", "data": {"value": 200}}
        ]
        
        formatted_data = {
            "records": raw_test_data,
            "format": "JSON",
            "validated": True
        }
        
        processed_data = {
            "integration_id": "INT-12345",
            "processed_at": datetime.now().isoformat(),
            "data": formatted_data
        }
        
        api_response = {
            "status": "success",
            "transaction_id": "TXN-67890",
            "message": "Data successfully integrated"
        }
        
        # Configure mocks
        feature_integration.ca001_connector.connect.return_value = True
        feature_integration.ca001_connector.is_connected = True
        feature_integration.ca001_connector.fetch_data.return_value = raw_test_data
        feature_integration.format_orchestrator.format_data.return_value = formatted_data
        feature_integration.integration_controller.process.return_value = processed_data
        feature_integration.system_api.send_data.return_value = api_response
        
        # Execute
        result = await feature_integration.process_data_flow(test_query)
        
        # Verify
        assert result["status"] == "success"
        assert "transaction_id" in result
        
        # Verify call chain
        feature_integration.ca001_connector.connect.assert_called_once()
        feature_integration.ca001_connector.fetch_data.assert_called_once_with(test_query["query"])
        feature_integration.format_orchestrator.format_data.assert_called_once_with(raw_test_data, "JSON")
        feature_integration.integration_controller.process.assert_called_once_with(formatted_data)
        feature_integration.system_api.send_data.assert_called_once_with(processed_data)

    @pytest.mark.asyncio
    async def test_connection_failure_handling(self, feature_integration):
        """Test 2: Handle connection failure at CA-001 Data Connector layer"""
        # Setup
        test_query = {"query": "SELECT * FROM ca001_data"}
        
        # Configure mock to fail
        feature_integration.ca001_connector.connect.side_effect = ConnectionError("Unable to connect to CA-001 system")
        
        # Execute and verify exception handling
        with pytest.raises(ConnectionError) as exc_info:
            await feature_integration.process_data_flow(test_query)
            
        assert "Unable to connect to CA-001 system" in str(exc_info.value)
        
        # Verify that subsequent layers were not called
        feature_integration.ca001_connector.fetch_data.assert_not_called()
        feature_integration.format_orchestrator.format_data.assert_not_called()
        feature_integration.integration_controller.process.assert_not_called()
        feature_integration.system_api.send_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_data_validation_failure(self, feature_integration):
        """Test 3: Handle data validation failure at Format Orchestrator layer"""
        # Setup
        test_query = {"query": "SELECT * FROM ca001_data", "format": "XML"}
        invalid_raw_data = [
            {"id": None, "data": {"value": 100}},  # Missing required timestamp
            {"timestamp": "2024-01-15T10:31:00", "data": {"value": 200}}  # Missing required id
        ]
        
        # Configure mocks
        feature_integration.ca001_connector.connect.return_value = True
        feature_integration.ca001_connector.is_connected = True
        feature_integration.ca001_connector.fetch_data.return_value = invalid_raw_data
        feature_integration.format_orchestrator.format_data.side_effect = ValidationError(
            "Data validation failed: Missing required fields"
        )
        
        # Execute and verify exception handling
        with pytest.raises(ValidationError) as exc_info:
            await feature_integration.process_data_flow(test_query)
            
        assert "Missing required fields" in str(exc_info.value)
        
        # Verify layers up to validation were called
        feature_integration.ca001_connector.fetch_data.assert_called_once()
        feature_integration.format_orchestrator.format_data.assert_called_once()
        
        # Verify subsequent layers were not called
        feature_integration.integration_controller.process.assert_not_called()
        feature_integration.system_api.send_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_api_authentication_failure_with_retry(self, feature_integration):
        """Test 4: Handle API authentication failure with retry mechanism"""
        # Setup
        test_query = {"query": "SELECT * FROM ca001_data"}
        raw_data = [{"id": "001", "timestamp": "2024-01-15T10:30:00", "data": {"value": 100}}]
        formatted_data = {"records": raw_data, "format": "JSON", "validated": True}
        processed_data = {"integration_id": "INT-12345", "data": formatted_data}
        
        # Configure mocks
        feature_integration.ca001_connector.connect.return_value = True
        feature_integration.ca001_connector.is_connected = True
        feature_integration.ca001_connector.fetch_data.return_value = raw_data
        feature_integration.format_orchestrator.format_data.return_value = formatted_data
        feature_integration.integration_controller.process.return_value = processed_data
        
        # First call fails with auth error, second succeeds after re-auth
        feature_integration.system_api.send_data.side_effect = [
            AuthenticationError("Invalid or expired token"),
            {"status": "success", "transaction_id": "TXN-99999"}
        ]
        
        # Add retry logic to feature integration
        async def process_with_retry(request_data):
            try:
                return await feature_integration.process_data_flow(request_data)
            except AuthenticationError:
                # Re-authenticate
                feature_integration.system_api.authenticate = Mock(return_value="new-token")
                feature_integration.system_api.authenticate()
                feature_integration.system_api.auth_token = "new-token"
                # Retry the process
                return await feature_integration.process_data_flow(request_data)
        
        # Execute
        result = await process_with_retry(test_query)
        
        # Verify
        assert result["status"] == "success"
        assert feature_integration.system_api.send_data.call_count == 2
        feature_integration.system_api.authenticate.assert_called_once()

    @pytest.mark.asyncio
    async def test_large_dataset_processing_with_batching(self, feature_integration):
        """Test 5: Process large dataset with automatic batching across layers"""
        # Setup - Create large dataset
        large_dataset = [
            {"id": f"ID-{i:04d}", "timestamp": f"2024-01-15T10:{i%60:02d}:00", 
             "data": {"value": i * 10, "category": f"CAT-{i % 5}"}}
            for i in range(1000)
        ]
        
        test_query = {"query": "SELECT * FROM ca001_large_table", "batch_size": 100}
        
        # Configure mocks for batch processing
        feature_integration.ca001_connector.connect.return_value = True
        feature_integration.ca001_connector.is_connected = True
        feature_integration.ca001_connector.fetch_data.return_value = large_dataset
        
        # Format orchestrator processes in batches
        def batch_format(data, format_type):
            return {
                "records": data,
                "format": format_type,
                "batch_info": {
                    "total_records": len(data),
                    "batch_size": 100,
                    "batches": (len(data) + 99) // 100
                },
                "validated": True
            }
        
        feature_integration.format_orchestrator.format_data.side_effect = batch_format
        
        # Integration controller adds batch tracking
        def process_batch(formatted_data):
            return {
                "integration_id": f"INT-BATCH-{datetime.now().timestamp()}",
                "batch_info": formatted_data.get("batch_info"),
                "processed_at": datetime.now().isoformat(),
                "data": formatted_data
            }
        
        feature_integration.integration_controller.process.side_effect = process_batch
        
        # API returns success for each batch
        api_responses = []
        for i in range(10):  # 10 batches of 100 records each
            api_responses.append({
                "status": "success",
                "batch_number": i + 1,
                "transaction_id": f"TXN-BATCH-{i+1:03d}",
                "records_processed": 100 if i < 9 else 100  # Last batch might have fewer
            })
        
        feature_integration.system_api.send_data.side_effect = api_responses
        
        # Execute - simulate batch processing
        all_results = []
        result = await feature_integration.process_data_flow(test_query)
        all_results.append(result)
        
        # For remaining batches
        for i in range(1, 10):
            feature_integration.system_api.send_data.side_effect = [api_responses[i]]
            result = await feature_integration.process_data_flow(test_query)
            all_results.append(result)
        
        # Verify
        assert len(all_results) == 10
        assert all(r["status"] == "success" for r in all_results)
        assert all("transaction_id" in r for r in all_results)
        
        # Verify batch processing
        total_records_processed = sum(r.get("records_processed", 0) for r in all_results)
        assert total_records_processed == 1000

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, feature_integration):
        """Test 6: Handle concurrent requests through all layers"""
        # Setup multiple concurrent requests
        requests = [
            {"query": f"SELECT * FROM ca001_data WHERE type='{t}'", "format": "JSON"}
            for t in ["A", "B", "C"]
        ]
        
        # Configure mocks for concurrent handling
        feature_integration.ca001_connector.connect.return_value = True
        feature_integration.ca001_connector.is_connected = True
        
        # Different data for each request
        data_responses = {
            "A": [{"id": "A001", "timestamp": "2024-01-15T10:00:00", "data": {"type": "A"}}],
            "B": [{"id": "B001", "timestamp": "2024-01-15T10:01:00", "data": {"type": "B"}}],
            "C": [{"id": "C001", "timestamp": "2024-01-15T10:02:00", "data": {"type": "C"}}]
        }
        
        def fetch_by_query(query):
            for type_key in data_responses.keys():
                if f"type='{type_key}'" in query:
                    return data_responses[type_key]
            return []
        
        feature_integration.ca001_connector.fetch_data.side_effect = fetch_by_query
        feature_integration.format_orchestrator.format_data.side_effect = lambda d, f: {"records": d, "format": f}
        feature_integration.integration_controller.process.side_effect = lambda d: {"processed": d}
        feature_integration.system_api.send_data.side_effect = lambda d: {"status": "success", "data": d}
        
        # Execute concurrent requests
        tasks = [feature_integration.process_data_flow(req) for req in requests]
        results = await asyncio.gather(*tasks)
        
        # Verify
        assert len(results) == 3
        assert all(r["status"] == "success" for r in results)
        assert feature_integration.ca001_connector.fetch_data.call_count == 3
        assert feature_integration.system_api.send_data.call_count == 3

    def test_layer_initialization_and_teardown(self, ca001_connector, format_orchestrator,
                                              integration_controller, system_api):
        """Test 7: Verify proper initialization and teardown of all layers"""
        # Test initialization
        class FeatureIntegrationLifecycle:
            def __init__(self):
                self.layers = []
                self.initialized = False
                
            def initialize_layers(self):
                """Initialize all layers in correct order"""
                # Layer 1: Initialize CA-001 connector
                ca001_connector.initialize()
                self.layers.append(ca001_connector)
                
                # Layer 2: Initialize format orchestrator
                format_orchestrator.initialize()
                format_orchestrator.register_formats(["JSON", "XML", "CSV"])
                self.layers.append(format_orchestrator)
                
                # Layer 3: Initialize integration controller
                integration_controller.initialize()
                integration_controller.register_handlers({
                    "error": self.handle_error,
                    "success": self.handle_success
                })
                self.layers.append(integration_controller)
                
                # Layer 4: Initialize system API
                system_api.initialize()
                system_api.set_endpoints({
                    "data": "/integration/data",
                    "status": "/integration/status"
                })
                self.layers.append(system_api)
                
                self.initialized = True
                return True
                
            def teardown_layers(self):
                """Teardown all layers in reverse order"""
                for layer in reversed(self.layers):
                    layer.cleanup()
                self.initialized = False
                
            def handle_error(self, error):
                pass
                
            def handle_success(self, result):
                pass
        
        # Execute initialization
        lifecycle = FeatureIntegrationLifecycle()
        init_result = lifecycle.initialize_layers()
        
        # Verify initialization
        assert init_result is True
        assert lifecycle.initialized is True
        assert len(lifecycle.layers) == 4
        
        # Verify initialization calls
        ca001_connector.initialize.assert_called_once()
        format_orchestrator.initialize.assert_called_once()
        format_orchestrator.register_formats.assert_called_once_with(["JSON", "XML", "CSV"])
        integration_controller.initialize.assert_called_once()
        integration_controller.register_handlers.assert_called_once()
        system_api.initialize.assert_called_once()
        system_api.set_endpoints.assert_called_once()
        
        # Execute teardown
        lifecycle.teardown_layers()
        
        # Verify teardown
        assert lifecycle.initialized is False
        for layer in [ca001_connector, format_orchestrator, integration_controller, system_api]:
            layer.cleanup.assert_called_once()


# Additional test utilities
class TestIntegrationHelpers:
    """Helper methods for integration testing"""
    
    @staticmethod
    def create_test_data(num_records: int) -> List[Dict[str, Any]]:
        """Create test data for integration tests"""
        return [
            {
                "id": f"TEST-{i:04d}",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "value": i * 10,
                    "status": "active" if i % 2 == 0 else "inactive"
                }
            }
            for i in range(num_records)
        ]
    
    @staticmethod
    def verify_data_integrity(original_data: List[Dict], processed_data: Dict) -> bool:
        """Verify data integrity through processing layers"""
        if "records" not in processed_data:
            return False
            
        processed_records = processed_data["records"]
        if len(processed_records) != len(original_data):
            return False
            
        for orig, proc in zip(original_data, processed_records):
            if orig["id"] != proc["id"]:
                return False
                
        return True


# Performance test for integration
@pytest.mark.performance
class TestIntegrationPerformance:
    """Performance tests for the integration"""
    
    @pytest.mark.asyncio
    async def test_high_throughput_processing(self, feature_integration):
        """Test system performance under high throughput"""
        import time
        
        # Setup
        num_requests = 100
        requests = [
            {"query": f"SELECT * FROM ca001_data LIMIT 10 OFFSET {i*10}"}
            for i in range(num_requests)
        ]
        
        # Configure mocks for fast processing
        feature_integration.ca001_connector.connect.return_value = True
        feature_integration.ca001_connector.is_connected = True
        feature_integration.ca001_connector.fetch_data.return_value = [{"id": "test", "data": {}}]
        feature_integration.format_orchestrator.format_data.return_value = {"records": [{"id": "test"}]}
        feature_integration.integration_controller.process.return_value = {"processed": True}
        feature_integration.system_api.send_data.return_value = {"status": "success"}
        
        # Execute and measure
        start_time = time.time()
        tasks = [feature_integration.process_data_flow(req) for req in requests]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Verify performance
        duration = end_time - start_time
        throughput = num_requests / duration
        
        assert len(results) == num_requests
        assert all(r["status"] == "success" for r in results)
        assert throughput > 50  # At least 50 requests per second
        
        print(f"Processed {num_requests} requests in {duration:.2f} seconds")
        print(f"Throughput: {throughput:.2f} requests/second")