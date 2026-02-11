import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Import the layers
from domain.regression_quantifier import RegressionQuantifier
from application.regression_service import RegressionService
from infrastructure.data_repository import DataRepository
from api.regression_controller import RegressionController, app
from infrastructure.logging_config import setup_logging

# Test fixtures
@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = Mock(spec=Session)
    return session

@pytest.fixture
def mock_data_repository(mock_db_session):
    """Create a mock data repository"""
    repo = Mock(spec=DataRepository)
    repo.session = mock_db_session
    return repo

@pytest.fixture
def regression_quantifier():
    """Create a regression quantifier instance"""
    return RegressionQuantifier()

@pytest.fixture
def regression_service(mock_data_repository, regression_quantifier):
    """Create a regression service with mocked dependencies"""
    service = RegressionService(mock_data_repository)
    service.quantifier = regression_quantifier
    return service

@pytest.fixture
def test_client():
    """Create a test client for the Flask API"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_backtest_data():
    """Create sample backtest data for testing"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    return pd.DataFrame({
        'date': dates,
        'actual_returns': np.random.randn(100) * 0.02,
        'predicted_returns': np.random.randn(100) * 0.02 + 0.001,
        'strategy_returns': np.random.randn(100) * 0.015
    })

class TestRegressionQuantificationIntegration:
    """Integration tests for the Regression Quantification Service"""

    def test_full_regression_analysis_workflow(self, regression_service, mock_data_repository, sample_backtest_data):
        """
        Test the complete workflow from data retrieval to regression analysis
        
        Integration Scenario: Domain ← Application ← Infrastructure
        Tests that regression analysis flows correctly through all layers
        """
        # Arrange
        strategy_id = "test_strategy_123"
        mock_data_repository.get_backtest_results.return_value = sample_backtest_data
        
        # Act
        result = regression_service.analyze_regression(
            strategy_id=strategy_id,
            start_date="2024-01-01",
            end_date="2024-04-10"
        )
        
        # Assert
        assert result is not None
        assert 'alpha' in result
        assert 'beta' in result
        assert 'r_squared' in result
        assert 'p_value' in result
        assert 'residual_analysis' in result
        
        # Verify data flow
        mock_data_repository.get_backtest_results.assert_called_once_with(
            strategy_id, "2024-01-01", "2024-04-10"
        )
        
        # Verify regression coefficients are reasonable
        assert isinstance(result['alpha'], float)
        assert isinstance(result['beta'], float)
        assert 0 <= result['r_squared'] <= 1
        assert 0 <= result['p_value'] <= 1

    def test_api_to_service_integration(self, test_client, mock_data_repository, sample_backtest_data):
        """
        Test API endpoint integration with service layer
        
        Integration Scenario: API → Application → Domain
        Tests HTTP request handling through to regression calculation
        """
        # Arrange
        with patch('api.regression_controller.regression_service') as mock_service:
            mock_service.analyze_regression.return_value = {
                'alpha': 0.001,
                'beta': 0.95,
                'r_squared': 0.85,
                'p_value': 0.001,
                'residual_analysis': {
                    'mean': 0.0001,
                    'std': 0.01,
                    'skewness': 0.1,
                    'kurtosis': 3.2
                }
            }
            
            # Act
            response = test_client.post('/api/v1/regression/analyze', 
                json={
                    'strategy_id': 'test_strategy_123',
                    'start_date': '2024-01-01',
                    'end_date': '2024-04-10',
                    'confidence_level': 0.95
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'data' in data
            assert data['data']['alpha'] == 0.001
            assert data['data']['beta'] == 0.95
            
            # Verify service was called correctly
            mock_service.analyze_regression.assert_called_once()

    def test_error_handling_across_layers(self, regression_service, mock_data_repository):
        """
        Test error propagation from infrastructure to application layer
        
        Integration Scenario: Infrastructure error → Application handling → Client response
        Tests that errors are properly caught and transformed across layers
        """
        # Arrange
        mock_data_repository.get_backtest_results.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            regression_service.analyze_regression(
                strategy_id="test_strategy_123",
                start_date="2024-01-01",
                end_date="2024-04-10"
            )
        
        assert "Database connection failed" in str(exc_info.value)
        mock_data_repository.get_backtest_results.assert_called_once()

    def test_rolling_regression_integration(self, regression_service, mock_data_repository, sample_backtest_data):
        """
        Test rolling regression analysis through multiple layers
        
        Integration Scenario: Application → Domain (rolling window) → Infrastructure
        Tests complex multi-period analysis workflow
        """
        # Arrange
        strategy_id = "test_strategy_123"
        mock_data_repository.get_backtest_results.return_value = sample_backtest_data
        
        # Act
        result = regression_service.calculate_rolling_regression(
            strategy_id=strategy_id,
            window_size=30,
            start_date="2024-01-01",
            end_date="2024-04-10"
        )
        
        # Assert
        assert result is not None
        assert 'timestamps' in result
        assert 'alphas' in result
        assert 'betas' in result
        assert 'r_squared_values' in result
        
        # Verify rolling windows were calculated
        assert len(result['timestamps']) > 0
        assert len(result['alphas']) == len(result['timestamps'])
        assert len(result['betas']) == len(result['timestamps'])
        assert len(result['r_squared_values']) == len(result['timestamps'])
        
        # Verify data repository was called
        mock_data_repository.get_backtest_results.assert_called_once()

    def test_residual_diagnostics_integration(self, regression_service, mock_data_repository, sample_backtest_data):
        """
        Test residual diagnostics calculation across layers
        
        Integration Scenario: Domain calculations → Application aggregation → API response
        Tests statistical diagnostics flow through the system
        """
        # Arrange
        strategy_id = "test_strategy_123"
        mock_data_repository.get_backtest_results.return_value = sample_backtest_data
        
        # Act
        result = regression_service.perform_residual_diagnostics(
            strategy_id=strategy_id,
            start_date="2024-01-01",
            end_date="2024-04-10"
        )
        
        # Assert
        assert result is not None
        assert 'normality_test' in result
        assert 'heteroscedasticity_test' in result
        assert 'autocorrelation_test' in result
        assert 'residual_plots' in result
        
        # Verify statistical test results
        assert 'statistic' in result['normality_test']
        assert 'p_value' in result['normality_test']
        assert isinstance(result['normality_test']['p_value'], float)
        
        # Verify data flow
        mock_data_repository.get_backtest_results.assert_called_once()

    def test_multi_strategy_comparison_integration(self, test_client):
        """
        Test multi-strategy regression comparison through API
        
        Integration Scenario: API → Application (parallel processing) → Domain → Infrastructure
        Tests handling multiple strategies simultaneously
        """
        # Arrange
        with patch('api.regression_controller.regression_service') as mock_service:
            mock_service.compare_strategies.return_value = {
                'strategies': {
                    'strategy_1': {'alpha': 0.001, 'beta': 0.95, 'r_squared': 0.85},
                    'strategy_2': {'alpha': 0.002, 'beta': 0.90, 'r_squared': 0.80}
                },
                'best_strategy': 'strategy_1',
                'comparison_metrics': {
                    'alpha_difference': 0.001,
                    'beta_difference': 0.05,
                    'r_squared_difference': 0.05
                }
            }
            
            # Act
            response = test_client.post('/api/v1/regression/compare',
                json={
                    'strategy_ids': ['strategy_1', 'strategy_2'],
                    'start_date': '2024-01-01',
                    'end_date': '2024-04-10',
                    'metric': 'r_squared'
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'strategies' in data['data']
            assert len(data['data']['strategies']) == 2
            assert data['data']['best_strategy'] == 'strategy_1'

    def test_caching_integration(self, regression_service, mock_data_repository, sample_backtest_data):
        """
        Test caching mechanism across layers
        
        Integration Scenario: Application (cache check) → Infrastructure → Domain
        Tests that repeated calls use cached results
        """
        # Arrange
        strategy_id = "test_strategy_123"
        mock_data_repository.get_backtest_results.return_value = sample_backtest_data
        
        # Enable caching in service
        regression_service.enable_caching = True
        regression_service._cache = {}
        
        # Act - First call
        result1 = regression_service.analyze_regression(
            strategy_id=strategy_id,
            start_date="2024-01-01",
            end_date="2024-04-10"
        )
        
        # Act - Second call (should use cache)
        result2 = regression_service.analyze_regression(
            strategy_id=strategy_id,
            start_date="2024-01-01",
            end_date="2024-04-10"
        )
        
        # Assert
        assert result1 == result2
        # Verify repository was called only once due to caching
        assert mock_data_repository.get_backtest_results.call_count == 1
        
        # Verify cache contains the result
        cache_key = f"{strategy_id}_2024-01-01_2024-04-10"
        assert cache_key in regression_service._cache

    def test_logging_integration(self, regression_service, mock_data_repository, sample_backtest_data, caplog):
        """
        Test logging integration across all layers
        
        Integration Scenario: All layers → Logging infrastructure
        Tests that important events are logged correctly
        """
        # Arrange
        import logging
        caplog.set_level(logging.INFO)
        strategy_id = "test_strategy_123"
        mock_data_repository.get_backtest_results.return_value = sample_backtest_data
        
        # Act
        result = regression_service.analyze_regression(
            strategy_id=strategy_id,
            start_date="2024-01-01",
            end_date="2024-04-10"
        )
        
        # Assert
        # Check that key events were logged
        log_messages = [record.message for record in caplog.records]
        
        # Verify logging at different stages
        assert any("Analyzing regression" in msg for msg in log_messages)
        assert any("strategy_id" in msg for msg in log_messages)
        
        # Verify result was computed successfully
        assert result is not None
        assert 'alpha' in result

@pytest.mark.integration
class TestEndToEndScenarios:
    """End-to-end integration scenarios"""
    
    def test_concurrent_regression_analysis(self, regression_service, mock_data_repository, sample_backtest_data):
        """
        Test concurrent regression analysis for multiple strategies
        
        Tests thread safety and parallel processing capabilities
        """
        # Arrange
        import concurrent.futures
        strategy_ids = [f"strategy_{i}" for i in range(5)]
        mock_data_repository.get_backtest_results.return_value = sample_backtest_data
        
        # Act
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for strategy_id in strategy_ids:
                future = executor.submit(
                    regression_service.analyze_regression,
                    strategy_id=strategy_id,
                    start_date="2024-01-01",
                    end_date="2024-04-10"
                )
                futures.append(future)
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Assert
        assert len(results) == 5
        for result in results:
            assert 'alpha' in result
            assert 'beta' in result
            assert 'r_squared' in result
        
        # Verify all strategies were processed
        assert mock_data_repository.get_backtest_results.call_count == 5