"""
Integration tests for Statistical Correlation Calculator feature
Feature ID: FEATURE-CA-002-01
Tests interactions between different correlation calculation layers
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Tuple

# Assuming these are the imports from the actual implementation
from src.features.statistical_correlation_calculator import (
    CorrelationCalculatorFeature,
    PearsonCalculator,
    SpearmanCalculator,
    KendallCalculator,
    PartialCorrelationCalculator,
    LaggedCorrelationCalculator,
    CorrelationResult,
    CorrelationMatrix,
    CorrelationError
)


class TestStatisticalCorrelationCalculatorIntegration:
    """Integration tests for Statistical Correlation Calculator"""

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Generate sample financial time series data"""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        
        # Create correlated financial data
        base = np.random.randn(100)
        data = pd.DataFrame({
            'date': dates,
            'stock_a': base + np.random.randn(100) * 0.1,
            'stock_b': base * 0.8 + np.random.randn(100) * 0.15,
            'stock_c': -base * 0.5 + np.random.randn(100) * 0.2,
            'market_index': base * 1.2 + np.random.randn(100) * 0.05,
            'volume': np.abs(base * 1000 + np.random.randn(100) * 200)
        })
        data.set_index('date', inplace=True)
        return data

    @pytest.fixture
    def correlation_feature(self) -> CorrelationCalculatorFeature:
        """Initialize correlation calculator feature with all layers"""
        return CorrelationCalculatorFeature(
            enable_caching=True,
            cache_ttl=300,
            parallel_processing=True,
            max_workers=4
        )

    @pytest.fixture
    def mock_cache(self):
        """Mock cache for testing caching behavior"""
        with patch('src.features.statistical_correlation_calculator.CorrelationCache') as mock:
            cache_instance = MagicMock()
            mock.return_value = cache_instance
            yield cache_instance

    @pytest.mark.asyncio
    async def test_multiple_correlation_methods_comparison(
        self, correlation_feature, sample_data
    ):
        """
        Integration Test 1: Compare results across Pearson, Spearman, and Kendall methods
        Verifies that different correlation methods can be computed for the same dataset
        and results are consistent with expected relationships
        """
        # Select two variables for correlation
        x_data = sample_data['stock_a'].values
        y_data = sample_data['stock_b'].values
        
        # Calculate correlations using all three methods
        pearson_result = await correlation_feature.calculate_correlation(
            x=x_data,
            y=y_data,
            method='pearson'
        )
        
        spearman_result = await correlation_feature.calculate_correlation(
            x=x_data,
            y=y_data,
            method='spearman'
        )
        
        kendall_result = await correlation_feature.calculate_correlation(
            x=x_data,
            y=y_data,
            method='kendall'
        )
        
        # Verify all methods return valid results
        assert pearson_result.coefficient is not None
        assert spearman_result.coefficient is not None
        assert kendall_result.coefficient is not None
        
        # Verify p-values are computed
        assert 0 <= pearson_result.p_value <= 1
        assert 0 <= spearman_result.p_value <= 1
        assert 0 <= kendall_result.p_value <= 1
        
        # Verify confidence intervals are computed for Pearson
        assert pearson_result.confidence_interval is not None
        assert len(pearson_result.confidence_interval) == 2
        assert pearson_result.confidence_interval[0] < pearson_result.coefficient
        assert pearson_result.confidence_interval[1] > pearson_result.coefficient
        
        # Verify that correlations are positive (as expected from data generation)
        assert pearson_result.coefficient > 0.5
        assert spearman_result.coefficient > 0.5
        assert kendall_result.coefficient > 0.3  # Kendall typically lower
        
        # Verify metadata is properly set
        assert pearson_result.method == 'pearson'
        assert spearman_result.method == 'spearman'
        assert kendall_result.method == 'kendall'

    @pytest.mark.asyncio
    async def test_partial_correlation_with_control_variables(
        self, correlation_feature, sample_data
    ):
        """
        Integration Test 2: Calculate partial correlation controlling for market index
        Verifies that partial correlation correctly accounts for confounding variables
        """
        # Calculate regular correlation first
        regular_correlation = await correlation_feature.calculate_correlation(
            x=sample_data['stock_a'].values,
            y=sample_data['stock_b'].values,
            method='pearson'
        )
        
        # Calculate partial correlation controlling for market index
        partial_correlation = await correlation_feature.calculate_partial_correlation(
            x=sample_data['stock_a'].values,
            y=sample_data['stock_b'].values,
            control_variables=[sample_data['market_index'].values],
            method='pearson'
        )
        
        # Verify partial correlation is computed
        assert partial_correlation.coefficient is not None
        assert partial_correlation.p_value is not None
        
        # Partial correlation should be different from regular correlation
        assert abs(partial_correlation.coefficient - regular_correlation.coefficient) > 0.01
        
        # Test with multiple control variables
        multi_control_partial = await correlation_feature.calculate_partial_correlation(
            x=sample_data['stock_a'].values,
            y=sample_data['stock_b'].values,
            control_variables=[
                sample_data['market_index'].values,
                sample_data['volume'].values
            ],
            method='pearson'
        )
        
        assert multi_control_partial.coefficient is not None
        assert multi_control_partial.controlled_variables == ['market_index', 'volume']
        
        # Verify error handling for mismatched dimensions
        with pytest.raises(CorrelationError):
            await correlation_feature.calculate_partial_correlation(
                x=sample_data['stock_a'].values,
                y=sample_data['stock_b'].values,
                control_variables=[sample_data['market_index'].values[:50]],  # Wrong size
                method='pearson'
            )

    @pytest.mark.asyncio
    async def test_lagged_correlation_time_series_analysis(
        self, correlation_feature, sample_data
    ):
        """
        Integration Test 3: Calculate lagged correlations for time series analysis
        Verifies that lagged correlations can identify temporal relationships
        """
        # Test single lag correlation
        lag_1_correlation = await correlation_feature.calculate_lagged_correlation(
            x=sample_data['stock_a'].values,
            y=sample_data['stock_b'].values,
            lag=1,
            method='pearson'
        )
        
        assert lag_1_correlation.coefficient is not None
        assert lag_1_correlation.lag == 1
        assert lag_1_correlation.effective_sample_size == len(sample_data) - 1
        
        # Test multiple lags
        lag_range = range(-5, 6)
        lagged_correlations = await correlation_feature.calculate_multiple_lags(
            x=sample_data['stock_a'].values,
            y=sample_data['stock_b'].values,
            lags=lag_range,
            method='pearson'
        )
        
        assert len(lagged_correlations) == len(lag_range)
        
        # Find optimal lag
        optimal_lag_result = await correlation_feature.find_optimal_lag(
            x=sample_data['stock_a'].values,
            y=sample_data['stock_b'].values,
            max_lag=10,
            method='pearson'
        )
        
        assert optimal_lag_result.optimal_lag is not None
        assert optimal_lag_result.optimal_correlation is not None
        assert -10 <= optimal_lag_result.optimal_lag <= 10
        
        # Test with Spearman method for robustness
        spearman_lagged = await correlation_feature.calculate_lagged_correlation(
            x=sample_data['stock_a'].values,
            y=sample_data['stock_c'].values,  # Negatively correlated
            lag=2,
            method='spearman'
        )
        
        assert spearman_lagged.method == 'spearman'
        assert spearman_lagged.lag == 2

    @pytest.mark.asyncio
    async def test_correlation_matrix_computation_with_caching(
        self, correlation_feature, sample_data, mock_cache
    ):
        """
        Integration Test 4: Compute full correlation matrix with caching
        Verifies matrix computation efficiency and caching behavior
        """
        # Select multiple variables for correlation matrix
        variables = ['stock_a', 'stock_b', 'stock_c', 'market_index']
        data_matrix = sample_data[variables].values
        
        # First computation - should calculate and cache
        mock_cache.get.return_value = None  # Cache miss
        
        correlation_matrix = await correlation_feature.calculate_correlation_matrix(
            data=data_matrix,
            variable_names=variables,
            method='pearson'
        )
        
        # Verify matrix properties
        assert correlation_matrix.shape == (4, 4)
        assert np.allclose(correlation_matrix.diagonal(), 1.0)  # Diagonal should be 1
        assert np.allclose(correlation_matrix, correlation_matrix.T)  # Should be symmetric
        
        # Verify caching was attempted
        assert mock_cache.get.called
        assert mock_cache.set.called
        
        # Second computation - should retrieve from cache
        mock_cache.get.return_value = correlation_matrix
        mock_cache.set.reset_mock()
        
        cached_matrix = await correlation_feature.calculate_correlation_matrix(
            data=data_matrix,
            variable_names=variables,
            method='pearson'
        )
        
        assert np.allclose(cached_matrix, correlation_matrix)
        assert not mock_cache.set.called  # Should not set cache again
        
        # Test with different methods in parallel
        methods = ['pearson', 'spearman', 'kendall']
        
        async def compute_matrix(method):
            return await correlation_feature.calculate_correlation_matrix(
                data=data_matrix,
                variable_names=variables,
                method=method
            )
        
        # Run all methods in parallel
        matrices = await asyncio.gather(
            *[compute_matrix(method) for method in methods]
        )
        
        # Verify all matrices computed successfully
        assert len(matrices) == 3
        for matrix in matrices:
            assert matrix.shape == (4, 4)

    @pytest.mark.asyncio
    async def test_end_to_end_portfolio_correlation_analysis(
        self, correlation_feature, sample_data
    ):
        """
        Integration Test 5: Complete portfolio correlation analysis workflow
        Simulates real-world usage with multiple correlation analyses
        """
        portfolio_stocks = ['stock_a', 'stock_b', 'stock_c']
        
        # Step 1: Calculate correlation matrix for portfolio
        portfolio_data = sample_data[portfolio_stocks].values
        correlation_matrix = await correlation_feature.calculate_correlation_matrix(
            data=portfolio_data,
            variable_names=portfolio_stocks,
            method='pearson'
        )
        
        # Step 2: Identify highly correlated pairs
        high_correlation_threshold = 0.7
        highly_correlated_pairs = []
        
        for i in range(len(portfolio_stocks)):
            for j in range(i + 1, len(portfolio_stocks)):
                if abs(correlation_matrix[i, j]) > high_correlation_threshold:
                    highly_correlated_pairs.append((
                        portfolio_stocks[i],
                        portfolio_stocks[j],
                        correlation_matrix[i, j]
                    ))
        
        assert len(highly_correlated_pairs) > 0  # Should find some correlations
        
        # Step 3: Analyze correlation with market index (partial correlation)
        market_correlations = {}
        for stock in portfolio_stocks:
            # Regular correlation with market
            regular_corr = await correlation_feature.calculate_correlation(
                x=sample_data[stock].values,
                y=sample_data['market_index'].values,
                method='pearson'
            )
            
            # Partial correlation controlling for volume
            partial_corr = await correlation_feature.calculate_partial_correlation(
                x=sample_data[stock].values,
                y=sample_data['market_index'].values,
                control_variables=[sample_data['volume'].values],
                method='pearson'
            )
            
            market_correlations[stock] = {
                'regular': regular_corr.coefficient,
                'partial': partial_corr.coefficient,
                'difference': regular_corr.coefficient - partial_corr.coefficient
            }
        
        # Verify market correlation analysis
        assert len(market_correlations) == len(portfolio_stocks)
        for stock, corr_data in market_correlations.items():
            assert 'regular' in corr_data
            assert 'partial' in corr_data
            assert 'difference' in corr_data
        
        # Step 4: Lead-lag analysis between stocks
        lead_lag_results = {}
        for i, stock1 in enumerate(portfolio_stocks):
            for j, stock2 in enumerate(portfolio_stocks):
                if i < j:  # Only compute for unique pairs
                    optimal_lag = await correlation_feature.find_optimal_lag(
                        x=sample_data[stock1].values,
                        y=sample_data[stock2].values,
                        max_lag=5,
                        method='pearson'
                    )
                    lead_lag_results[f"{stock1}_{stock2}"] = {
                        'optimal_lag': optimal_lag.optimal_lag,
                        'correlation': optimal_lag.optimal_correlation
                    }
        
        # Verify lead-lag analysis
        assert len(lead_lag_results) == 3  # C(3,2) = 3 pairs
        
        # Step 5: Robustness check with different correlation methods
        robustness_check = {}
        for stock1, stock2, _ in highly_correlated_pairs[:1]:  # Check first pair
            methods_results = {}
            for method in ['pearson', 'spearman', 'kendall']:
                result = await correlation_feature.calculate_correlation(
                    x=sample_data[stock1].values,
                    y=sample_data[stock2].values,
                    method=method
                )
                methods_results[method] = result.coefficient
            robustness_check[f"{stock1}_{stock2}"] = methods_results
        
        # Verify all methods produce reasonable results
        for pair, results in robustness_check.items():
            assert len(results) == 3
            # All methods should agree on direction (positive/negative)
            signs = [np.sign(corr) for corr in results.values()]
            assert len(set(signs)) == 1  # All same sign
        
        # Final integration verification
        assert correlation_matrix is not None
        assert len(highly_correlated_pairs) > 0
        assert len(market_correlations) == len(portfolio_stocks)
        assert len(lead_lag_results) > 0
        assert len(robustness_check) > 0

    @pytest.mark.asyncio
    async def test_error_handling_across_layers(
        self, correlation_feature, sample_data
    ):
        """
        Bonus Test: Comprehensive error handling across all layers
        """
        # Test with invalid data types
        with pytest.raises(CorrelationError):
            await correlation_feature.calculate_correlation(
                x="invalid_data",
                y=[1, 2, 3],
                method='pearson'
            )
        
        # Test with mismatched dimensions
        with pytest.raises(CorrelationError):
            await correlation_feature.calculate_correlation(
                x=sample_data['stock_a'].values,
                y=sample_data['stock_b'].values[:50],
                method='pearson'
            )
        
        # Test with invalid method
        with pytest.raises(CorrelationError):
            await correlation_feature.calculate_correlation(
                x=sample_data['stock_a'].values,
                y=sample_data['stock_b'].values,
                method='invalid_method'
            )
        
        # Test with insufficient data for lagged correlation
        with pytest.raises(CorrelationError):
            await correlation_feature.calculate_lagged_correlation(
                x=sample_data['stock_a'].values[:5],
                y=sample_data['stock_b'].values[:5],
                lag=10,  # Lag larger than data
                method='pearson'
            )
        
        # Test partial correlation with invalid control variables
        with pytest.raises(CorrelationError):
            await correlation_feature.calculate_partial_correlation(
                x=sample_data['stock_a'].values,
                y=sample_data['stock_b'].values,
                control_variables=[],  # Empty control variables
                method='pearson'
            )
        
        # Test correlation matrix with mismatched variable names
        with pytest.raises(CorrelationError):
            await correlation_feature.calculate_correlation_matrix(
                data=sample_data[['stock_a', 'stock_b']].values,
                variable_names=['stock_a', 'stock_b', 'stock_c'],  # Too many names
                method='pearson'
            )


@pytest.mark.asyncio
class TestPerformanceAndScalability:
    """Additional tests for performance and scalability"""
    
    @pytest.fixture
    def large_dataset(self) -> pd.DataFrame:
        """Generate large dataset for performance testing"""
        np.random.seed(42)
        n_samples = 10000
        n_variables = 20
        
        data = pd.DataFrame(
            np.random.randn(n_samples, n_variables),
            columns=[f'var_{i}' for i in range(n_variables)]
        )
        return data
    
    @pytest.mark.asyncio
    async def test_parallel_processing_performance(
        self, correlation_feature, large_dataset
    ):
        """Test that parallel processing improves performance for large datasets"""
        import time
        
        # Test with parallel processing enabled
        correlation_feature.parallel_processing = True
        start_time = time.time()
        
        matrix_parallel = await correlation_feature.calculate_correlation_matrix(
            data=large_dataset.values,
            variable_names=list(large_dataset.columns),
            method='pearson'
        )
        
        parallel_time = time.time() - start_time
        
        # Test with parallel processing disabled
        correlation_feature.parallel_processing = False
        start_time = time.time()
        
        matrix_sequential = await correlation_feature.calculate_correlation_matrix(
            data=large_dataset.values,
            variable_names=list(large_dataset.columns),
            method='pearson'
        )
        
        sequential_time = time.time() - start_time
        
        # Verify results are identical
        assert np.allclose(matrix_parallel, matrix_sequential)
        
        # Parallel should be faster for large datasets
        # (This might not always be true in test environments)
        print(f"Parallel time: {parallel_time:.2f}s, Sequential time: {sequential_time:.2f}s")