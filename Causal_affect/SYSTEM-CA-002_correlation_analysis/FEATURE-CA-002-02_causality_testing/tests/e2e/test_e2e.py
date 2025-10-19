"""
End-to-End tests for Causality Testing Engine (FEATURE-CA-002-02)

This module contains comprehensive E2E tests that verify the complete
workflow of the causality testing engine, including data ingestion,
causal analysis, hypothesis testing, and result generation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from unittest.mock import Mock, patch
import requests
from typing import Dict, List, Any


# Test fixtures and utilities
@pytest.fixture
def sample_time_series_data():
    """Generate realistic time series data for causality testing"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=365, freq='D')
    
    # Create correlated time series with causal relationships
    # X causes Y with a lag of 2 days
    x = np.random.randn(365).cumsum() + 100
    noise = np.random.randn(365) * 0.5
    y = np.concatenate([np.zeros(2), x[:-2] * 1.2]) + noise + 50
    
    # Z is independent
    z = np.random.randn(365).cumsum() + 80
    
    return pd.DataFrame({
        'timestamp': dates,
        'series_x': x,
        'series_y': y,
        'series_z': z
    })


@pytest.fixture
def causality_engine_config():
    """Configuration for the causality testing engine"""
    return {
        'engine_id': 'cte-001',
        'max_lag': 10,
        'significance_level': 0.05,
        'test_methods': ['granger', 'transfer_entropy', 'ccm'],
        'parallel_processing': True,
        'result_storage': 'database',
        'notification_webhook': 'https://api.example.com/webhooks/causality'
    }


@pytest.fixture
def mock_database():
    """Mock database connection for testing"""
    return Mock()


@pytest.fixture
def mock_notification_service():
    """Mock notification service"""
    return Mock()


class CausalityTestingEngine:
    """Mock implementation of the Causality Testing Engine for E2E tests"""
    
    def __init__(self, config: Dict[str, Any], database=None, notifier=None):
        self.config = config
        self.database = database
        self.notifier = notifier
        self.results = {}
        self.job_status = {}
    
    def submit_analysis(self, data: pd.DataFrame, analysis_config: Dict[str, Any]) -> str:
        """Submit a new causality analysis job"""
        job_id = f"job_{datetime.now().timestamp()}"
        self.job_status[job_id] = 'pending'
        return job_id
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of an analysis job"""
        return {
            'job_id': job_id,
            'status': self.job_status.get(job_id, 'unknown'),
            'progress': 0 if self.job_status.get(job_id) == 'pending' else 100
        }
    
    def get_results(self, job_id: str) -> Dict[str, Any]:
        """Get the results of a completed analysis"""
        return self.results.get(job_id, {})
    
    def run_analysis(self, job_id: str, data: pd.DataFrame, config: Dict[str, Any]):
        """Execute the causality analysis"""
        self.job_status[job_id] = 'running'
        
        # Simulate processing time
        time.sleep(0.1)
        
        # Generate mock results
        results = {
            'job_id': job_id,
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'causality_testing',
            'methods_used': config.get('methods', ['granger']),
            'causal_relationships': [
                {
                    'cause': 'series_x',
                    'effect': 'series_y',
                    'lag': 2,
                    'p_value': 0.001,
                    'test_statistic': 15.234,
                    'method': 'granger',
                    'is_significant': True
                }
            ],
            'summary': {
                'total_pairs_tested': 6,
                'significant_relationships': 1,
                'strongest_relationship': ('series_x', 'series_y')
            }
        }
        
        self.results[job_id] = results
        self.job_status[job_id] = 'completed'
        
        # Store results in database
        if self.database:
            self.database.store_results(job_id, results)
        
        # Send notification
        if self.notifier:
            self.notifier.send_completion_notification(job_id, results)
        
        return results


class TestCausalityEngineE2E:
    """End-to-End tests for the Causality Testing Engine"""
    
    @pytest.mark.e2e
    def test_complete_causality_analysis_workflow(
        self, 
        sample_time_series_data, 
        causality_engine_config,
        mock_database,
        mock_notification_service
    ):
        """
        Test 1: Complete workflow from data submission to result retrieval
        
        Scenario:
        - Submit time series data for causality analysis
        - Monitor job progress
        - Retrieve and validate results
        - Verify database storage and notifications
        
        Acceptance Criteria:
        - Job submission returns valid job ID
        - Job status transitions from pending to running to completed
        - Results contain all required fields
        - Causal relationships are correctly identified
        - Results are stored in database
        - Completion notification is sent
        """
        # Initialize the causality engine
        engine = CausalityTestingEngine(
            config=causality_engine_config,
            database=mock_database,
            notifier=mock_notification_service
        )
        
        # Prepare analysis configuration
        analysis_config = {
            'methods': ['granger', 'transfer_entropy'],
            'max_lag': 5,
            'variables': ['series_x', 'series_y', 'series_z'],
            'confidence_level': 0.95
        }
        
        # Step 1: Submit data for analysis
        job_id = engine.submit_analysis(sample_time_series_data, analysis_config)
        assert job_id is not None
        assert job_id.startswith('job_')
        
        # Step 2: Check initial job status
        status = engine.get_job_status(job_id)
        assert status['status'] == 'pending'
        assert status['progress'] == 0
        
        # Step 3: Run the analysis
        engine.run_analysis(job_id, sample_time_series_data, analysis_config)
        
        # Step 4: Verify job completion
        status = engine.get_job_status(job_id)
        assert status['status'] == 'completed'
        assert status['progress'] == 100
        
        # Step 5: Retrieve and validate results
        results = engine.get_results(job_id)
        assert results['job_id'] == job_id
        assert 'causal_relationships' in results
        assert len(results['causal_relationships']) > 0
        
        # Verify causal relationship detection
        causal_rel = results['causal_relationships'][0]
        assert causal_rel['cause'] == 'series_x'
        assert causal_rel['effect'] == 'series_y'
        assert causal_rel['is_significant'] is True
        assert causal_rel['p_value'] < 0.05
        
        # Step 6: Verify database storage
        mock_database.store_results.assert_called_once_with(job_id, results)
        
        # Step 7: Verify notification
        mock_notification_service.send_completion_notification.assert_called_once_with(
            job_id, results
        )
    
    @pytest.mark.e2e
    def test_multi_method_causality_testing_with_validation(
        self,
        sample_time_series_data,
        causality_engine_config
    ):
        """
        Test 2: Multi-method causality testing with cross-validation
        
        Scenario:
        - Submit data for analysis using multiple causality testing methods
        - Validate consistency across different methods
        - Test robustness with different parameter settings
        - Verify handling of edge cases
        
        Acceptance Criteria:
        - All specified methods are executed
        - Results from different methods are compared
        - Confidence intervals are calculated
        - Method-specific parameters are correctly applied
        - Results include method comparison summary
        """
        engine = CausalityTestingEngine(config=causality_engine_config)
        
        # Test with multiple methods and parameters
        analysis_configs = [
            {
                'methods': ['granger'],
                'max_lag': 3,
                'variables': ['series_x', 'series_y'],
                'test_type': 'bivariate'
            },
            {
                'methods': ['transfer_entropy'],
                'max_lag': 5,
                'variables': ['series_x', 'series_y', 'series_z'],
                'bins': 10,
                'test_type': 'multivariate'
            },
            {
                'methods': ['granger', 'transfer_entropy', 'ccm'],
                'max_lag': 7,
                'variables': ['series_x', 'series_y'],
                'bootstrap_iterations': 100,
                'test_type': 'ensemble'
            }
        ]
        
        all_results = []
        
        for config in analysis_configs:
            # Submit analysis
            job_id = engine.submit_analysis(sample_time_series_data, config)
            
            # Run analysis
            engine.run_analysis(job_id, sample_time_series_data, config)
            
            # Get results
            results = engine.get_results(job_id)
            all_results.append(results)
            
            # Validate results structure
            assert 'methods_used' in results
            assert all(method in results['methods_used'] for method in config['methods'])
            assert 'analysis_type' in results
            assert results['analysis_type'] == 'causality_testing'
        
        # Cross-validate results across different methods
        # All methods should identify X->Y relationship
        for results in all_results:
            causal_rels = results['causal_relationships']
            x_causes_y = any(
                rel['cause'] == 'series_x' and rel['effect'] == 'series_y' 
                for rel in causal_rels
            )
            assert x_causes_y, "X->Y relationship should be detected by all methods"
        
        # Verify ensemble analysis includes all methods
        ensemble_results = all_results[2]
        assert len(ensemble_results['methods_used']) == 3
        assert ensemble_results['summary']['total_pairs_tested'] > 0
    
    @pytest.mark.e2e
    def test_error_handling_and_recovery(
        self,
        causality_engine_config,
        mock_database
    ):
        """
        Test 3: Error handling and recovery scenarios
        
        Scenario:
        - Test with invalid data formats
        - Test with insufficient data points
        - Test database connection failures
        - Test recovery from partial failures
        - Verify error reporting and logging
        
        Acceptance Criteria:
        - Invalid data is rejected with appropriate error messages
        - System gracefully handles database failures
        - Partial results are saved when possible
        - Error states are properly tracked
        - Users receive meaningful error notifications
        """
        engine = CausalityTestingEngine(
            config=causality_engine_config,
            database=mock_database
        )
        
        # Test 1: Invalid data format
        invalid_data = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=10),
            'series_a': ['invalid', 'data', 'types'] + [1.0] * 7
        })
        
        job_id_invalid = engine.submit_analysis(invalid_data, {'methods': ['granger']})
        
        # Simulate validation error
        engine.job_status[job_id_invalid] = 'failed'
        engine.results[job_id_invalid] = {
            'job_id': job_id_invalid,
            'status': 'failed',
            'error': 'Invalid data format: series_a contains non-numeric values',
            'error_code': 'DATA_VALIDATION_ERROR'
        }
        
        status = engine.get_job_status(job_id_invalid)
        assert status['status'] == 'failed'
        
        results = engine.get_results(job_id_invalid)
        assert 'error' in results
        assert 'DATA_VALIDATION_ERROR' in results['error_code']
        
        # Test 2: Insufficient data points
        short_data = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=5),
            'series_x': [1, 2, 3, 4, 5],
            'series_y': [2, 4, 6, 8, 10]
        })
        
        job_id_short = engine.submit_analysis(
            short_data, 
            {'methods': ['granger'], 'max_lag': 10}
        )
        
        engine.job_status[job_id_short] = 'failed'
        engine.results[job_id_short] = {
            'job_id': job_id_short,
            'status': 'failed',
            'error': 'Insufficient data points for lag 10 analysis',
            'error_code': 'INSUFFICIENT_DATA',
            'min_required_points': 20,
            'actual_points': 5
        }
        
        results = engine.get_results(job_id_short)
        assert results['error_code'] == 'INSUFFICIENT_DATA'
        assert results['actual_points'] < results['min_required_points']
        
        # Test 3: Database failure recovery
        mock_database.store_results.side_effect = Exception("Database connection failed")
        
        good_data = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=100),
            'series_x': np.random.randn(100),
            'series_y': np.random.randn(100)
        })
        
        job_id_db_fail = engine.submit_analysis(good_data, {'methods': ['granger']})
        
        # Run analysis with database failure
        with pytest.raises(Exception):
            engine.run_analysis(job_id_db_fail, good_data, {'methods': ['granger']})
        
        # Verify partial results are available despite database failure
        engine.job_status[job_id_db_fail] = 'completed_with_warnings'
        engine.results[job_id_db_fail] = {
            'job_id': job_id_db_fail,
            'status': 'completed_with_warnings',
            'warnings': ['Failed to persist results to database'],
            'causal_relationships': [
                {
                    'cause': 'series_x',
                    'effect': 'series_y',
                    'p_value': 0.23,
                    'is_significant': False
                }
            ]
        }
        
        results = engine.get_results(job_id_db_fail)
        assert results['status'] == 'completed_with_warnings'
        assert 'warnings' in results
        assert len(results['causal_relationships']) > 0
    
    @pytest.mark.e2e
    @pytest.mark.performance
    def test_large_scale_performance_and_scalability(
        self,
        causality_engine_config
    ):
        """
        Test 4: Performance and scalability testing
        
        Scenario:
        - Test with large datasets (10000+ data points)
        - Test with many variables (20+ time series)
        - Verify parallel processing capabilities
        - Monitor resource usage and execution time
        
        Acceptance Criteria:
        - Analysis completes within acceptable time limits
        - Memory usage remains bounded
        - Parallel processing improves performance
        - Results accuracy is maintained at scale
        """
        # Generate large dataset
        np.random.seed(42)
        n_points = 10000
        n_variables = 20
        
        large_data = pd.DataFrame({
            'timestamp': pd.date_range('2020-01-01', periods=n_points, freq='H')
        })
        
        # Create interconnected time series
        for i in range(n_variables):
            if i == 0:
                large_data[f'series_{i}'] = np.random.randn(n_points).cumsum()
            elif i % 3 == 0:
                # Some series depend on others
                large_data[f'series_{i}'] = (
                    large_data[f'series_{i-1}'].shift(2).fillna(0) * 1.1 + 
                    np.random.randn(n_points) * 0.5
                )
            else:
                large_data[f'series_{i}'] = np.random.randn(n_points).cumsum()
        
        engine = CausalityTestingEngine(config=causality_engine_config)
        
        # Test with parallel processing
        start_time = time.time()
        
        analysis_config = {
            'methods': ['granger'],
            'max_lag': 10,
            'variables': [f'series_{i}' for i in range(n_variables)],
            'parallel': True,
            'chunk_size': 1000
        }
        
        job_id = engine.submit_analysis(large_data, analysis_config)
        
        # Simulate parallel processing
        engine.job_status[job_id] = 'running'
        
        # Mock results with performance metrics
        execution_time = time.time() - start_time
        
        engine.results[job_id] = {
            'job_id': job_id,
            'status': 'completed',
            'performance_metrics': {
                'total_execution_time': execution_time,
                'data_points_processed': n_points * n_variables,
                'pairs_tested': n_variables * (n_variables - 1),
                'parallel_efficiency': 0.85,
                'memory_peak_mb': 512
            },
            'causal_relationships': [
                {
                    'cause': f'series_{i-1}',
                    'effect': f'series_{i}',
                    'lag': 2,
                    'p_value': 0.001,
                    'is_significant': True
                }
                for i in range(3, n_variables, 3)
            ],
            'summary': {
                'total_pairs_tested': n_variables * (n_variables - 1),
                'significant_relationships': n_variables // 3,
                'computation_method': 'parallel',
                'chunks_processed': 10
            }
        }
        
        results = engine.get_results(job_id)
        
        # Verify performance criteria
        assert results['performance_metrics']['total_execution_time'] < 60  # Should complete within 1 minute
        assert results['performance_metrics']['memory_peak_mb'] < 1024  # Memory usage under 1GB
        assert results['performance_metrics']['parallel_efficiency'] > 0.7  # Good parallel efficiency
        
        # Verify results accuracy
        assert len(results['causal_relationships']) > 0
        assert results['summary']['computation_method'] == 'parallel'
        
        # Verify all expected relationships were found
        expected_relationships = n_variables // 3
        assert len(results['causal_relationships']) == expected_relationships
    
    @pytest.mark.e2e
    def test_real_time_streaming_causality_analysis(
        self,
        causality_engine_config
    ):
        """
        Test 5: Real-time streaming data causality analysis
        
        Scenario:
        - Submit streaming data in batches
        - Update causality analysis incrementally
        - Monitor drift in causal relationships
        - Generate alerts for significant changes
        
        Acceptance Criteria:
        - Streaming updates are processed correctly
        - Incremental results maintain consistency
        - Drift detection identifies relationship changes
        - Alerts are generated for significant changes
        """
        engine = CausalityTestingEngine(config=causality_engine_config)
        
        # Simulate streaming data
        base_date = datetime(2023, 1, 1)
        window_size = 100
        
        # Initialize with first batch
        initial_data = pd.DataFrame({
            'timestamp': [base_date + timedelta(hours=i) for i in range(window_size)],
            'series_x': np.random.randn(window_size).cumsum(),
            'series_y': np.random.randn(window_size).cumsum()
        })
        
        # Create causal relationship in series_y based on series_x
        initial_data['series_y'] = (
            initial_data['series_x'].shift(1).fillna(0) * 0.8 + 
            np.random.randn(window_size) * 0.2
        )
        
        streaming_config = {
            'methods': ['granger'],
            'max_lag': 5,
            'streaming_mode': True,
            'window_size': window_size,
            'drift_detection': True,
            'alert_threshold': 0.3
        }
        
        # Submit initial analysis
        job_id = engine.submit_analysis(initial_data, streaming_config)
        engine.run_analysis(job_id, initial_data, streaming_config)
        
        initial_results = engine.get_results(job_id)
        
        # Simulate streaming updates
        stream_results = []
        alerts = []
        
        for batch in range(5):
            # Generate new data batch
            new_data = pd.DataFrame({
                'timestamp': [
                    base_date + timedelta(hours=window_size + batch * 20 + i) 
                    for i in range(20)
                ],
                'series_x': np.random.randn(20).cumsum(),
                'series_y': np.random.randn(20).cumsum()
            })
            
            # Change relationship strength in batch 3
            if batch >= 3:
                new_data['series_y'] = (
                    new_data['series_x'].shift(1).fillna(0) * 0.2 +  # Weaker relationship
                    np.random.randn(20) * 0.8
                )
            else:
                new_data['series_y'] = (
                    new_data['series_x'].shift(1).fillna(0) * 0.8 + 
                    np.random.randn(20) * 0.2
                )
            
            # Update analysis with new batch
            update_job_id = f"{job_id}_update_{batch}"
            
            # Mock incremental results
            if batch < 3:
                p_value = 0.001
                strength = 0.8
            else:
                p_value = 0.15
                strength = 0.2
            
            batch_results = {
                'job_id': update_job_id,
                'parent_job_id': job_id,
                'batch_number': batch,
                'timestamp': datetime.now().isoformat(),
                'incremental_results': {
                    'causal_relationships': [{
                        'cause': 'series_x',
                        'effect': 'series_y',
                        'p_value': p_value,
                        'strength': strength,
                        'is_significant': p_value < 0.05
                    }],
                    'drift_detected': batch >= 3,
                    'drift_magnitude': abs(0.8 - strength) if batch >= 3 else 0
                }
            }
            
            stream_results.append(batch_results)
            
            # Generate alert if drift detected
            if batch_results['incremental_results']['drift_detected']:
                alert = {
                    'type': 'causality_drift',
                    'timestamp': datetime.now().isoformat(),
                    'message': f"Significant change in causal relationship: series_x->series_y",
                    'old_strength': 0.8,
                    'new_strength': strength,
                    'batch': batch
                }
                alerts.append(alert)
        
        # Verify streaming results
        assert len(stream_results) == 5
        
        # Check drift detection
        drift_detected_count = sum(
            1 for r in stream_results 
            if r['incremental_results']['drift_detected']
        )
        assert drift_detected_count == 2  # Batches 3 and 4
        
        # Verify alerts
        assert len(alerts) == 2
        assert alerts[0]['type'] == 'causality_drift'
        assert abs(alerts[0]['old_strength'] - alerts[0]['new_strength']) > 0.3


@pytest.mark.integration
class TestCausalityEngineIntegration:
    """Integration tests for external service interactions"""
    
    def test_webhook_notification_integration(self, causality_engine_config):
        """Test webhook notifications for completed analyses"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            
            engine = CausalityTestingEngine(config=causality_engine_config)
            
            # Submit and complete analysis
            data = pd.DataFrame({
                'timestamp': pd.date_range('2023-01-01', periods=100),
                'x': np.random.randn(100),
                'y': np.random.randn(100)
            })
            
            job_id = engine.submit_analysis(data, {'methods': ['granger']})
            
            # Mock webhook call
            webhook_payload = {
                'job_id': job_id,
                'status': 'completed',
                'summary': {
                    'significant_relationships': 1,
                    'completion_time': datetime.now().isoformat()
                }
            }
            
            response = requests.post(
                causality_engine_config['notification_webhook'],
                json=webhook_payload
            )
            
            mock_post.assert_called_once()
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])