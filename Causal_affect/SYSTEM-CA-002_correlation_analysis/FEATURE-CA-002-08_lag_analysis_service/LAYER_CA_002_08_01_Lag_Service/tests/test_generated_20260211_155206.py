import pytest
import unittest.mock
import sys
import os
import subprocess
import pathlib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class TestCalculateLagCurveReturnsCorrectLength:
    """Test that calculate_lag_curve returns arrays of correct length matching max_lag+1"""
    
    def test_lag_curve_length_matches_max_lag_plus_one(self):
        """Test that returned arrays have length of max_lag + 1"""
        from lag_analysis_service import LagService
        
        service = LagService()
        data1 = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        data2 = pd.Series([2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        max_lag = 5
        
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1, data2, max_lag)
        
        assert len(lag_days) == max_lag + 1
        assert len(correlations) == max_lag + 1
        assert False  # RED phase - expected to fail
    
    def test_different_max_lag_values(self):
        """Test with various max_lag values"""
        from lag_analysis_service import LagService
        
        service = LagService()
        data1 = pd.Series(range(20))
        data2 = pd.Series(range(1, 21))
        
        for max_lag in [3, 7, 10, 15]:
            lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1, data2, max_lag)
            assert len(lag_days) == max_lag + 1
            assert len(correlations) == max_lag + 1
        
        assert False  # RED phase - expected to fail


class TestLagDaysArraySequential:
    """Test that lag_days array is sequential from 0 to max_lag"""
    
    def test_lag_days_starts_at_zero(self):
        """Test that lag_days array starts with 0"""
        from lag_analysis_service import LagService
        
        service = LagService()
        data1 = pd.Series([1, 2, 3, 4, 5])
        data2 = pd.Series([2, 3, 4, 5, 6])
        max_lag = 3
        
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1, data2, max_lag)
        
        assert lag_days[0] == 0
        assert False  # RED phase - expected to fail
    
    def test_lag_days_sequential_values(self):
        """Test that lag_days contains sequential integers"""
        from lag_analysis_service import LagService
        
        service = LagService()
        data1 = pd.Series(range(10))
        data2 = pd.Series(range(1, 11))
        max_lag = 5
        
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1, data2, max_lag)
        
        expected = list(range(max_lag + 1))
        assert list(lag_days) == expected
        assert False  # RED phase - expected to fail
    
    def test_lag_days_ends_at_max_lag(self):
        """Test that lag_days array ends with max_lag value"""
        from lag_analysis_service import LagService
        
        service = LagService()
        data1 = pd.Series([1, 2, 3, 4, 5, 6, 7])
        data2 = pd.Series([2, 3, 4, 5, 6, 7, 8])
        max_lag = 4
        
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1, data2, max_lag)
        
        assert lag_days[-1] == max_lag
        assert False  # RED phase - expected to fail


class TestOptimalLagCorrespondsToHighestCorrelation:
    """Test that optimal_lag corresponds to lag with highest absolute correlation"""
    
    def test_optimal_lag_is_highest_positive_correlation(self):
        """Test optimal lag selection with positive correlations"""
        from lag_analysis_service import LagService
        
        service = LagService()
        # Create data where lag 2 should have highest correlation
        data1 = pd.Series([1, 2, 3, 4, 5, 6, 7, 8])
        data2 = pd.Series([0, 0, 1, 2, 3, 4, 5, 6])  # Shifted by 2
        max_lag = 5
        
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1, data2, max_lag)
        
        assert optimal_lag == 2
        assert correlations[optimal_lag] == max(correlations)
        assert False  # RED phase - expected to fail
    
    def test_optimal_lag_is_highest_negative_correlation(self):
        """Test optimal lag selection with negative correlations"""
        from lag_analysis_service import LagService
        
        service = LagService()
        # Create data with negative correlation
        data1 = pd.Series([1, 2, 3, 4, 5, 6, 7, 8])
        data2 = pd.Series([8, 7, 6, 5, 4, 3, 2, 1])  # Inverse relationship
        max_lag = 3
        
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1, data2, max_lag)
        
        max_abs_corr_idx = np.argmax(np.abs(correlations))
        assert optimal_lag == max_abs_corr_idx
        assert False  # RED phase - expected to fail
    
    def test_optimal_lag_uses_absolute_value(self):
        """Test that optimal lag uses absolute correlation value"""
        from lag_analysis_service import LagService
        
        service = LagService()
        # Create data with mixed positive and negative correlations
        data1 = pd.Series([1, -1, 1, -1, 1, -1, 1, -1, 1, -1])
        data2 = pd.Series([-1, 1, -1, 1, -1, 1, -1, 1, -1, 1])
        max_lag = 4
        
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1, data2, max_lag)
        
        abs_correlations = np.abs(correlations)
        assert abs_correlations[optimal_lag] == np.max(abs_correlations)
        assert False  # RED phase - expected to fail


class TestHandlesMissingDataGracefully:
    """Test that the service handles missing data gracefully with meaningful error"""
    
    def test_nan_values_in_data1(self):
        """Test handling of NaN values in first dataset"""
        from lag_analysis_service import LagService
        
        service = LagService()
        data1 = pd.Series([1, 2, np.nan, 4, 5])
        data2 = pd.Series([2, 3, 4, 5, 6])
        max_lag = 2
        
        with pytest.raises(ValueError, match="missing.*data"):
            service.calculate_lag_curve(data1, data2, max_lag)
        
        assert False  # RED phase - expected to fail
    
    def test_nan_values_in_data2(self):
        """Test handling of NaN values in second dataset"""
        from lag_analysis_service import LagService
        
        service = LagService()
        data1 = pd.Series([1, 2, 3, 4, 5])
        data2 = pd.Series([2, np.nan, 4, 5, 6])
        max_lag = 2
        
        with pytest.raises(ValueError, match="missing.*data"):
            service.calculate_lag_curve(data1, data2, max_lag)
        
        assert False  # RED phase - expected to fail
    
    def test_empty_series(self):
        """Test handling of empty data series"""
        from lag_analysis_service import LagService
        
        service = LagService()
        data1 = pd.Series([])
        data2 = pd.Series([])
        max_lag = 2
        
        with pytest.raises(ValueError, match="empty|missing"):
            service.calculate_lag_curve(data1, data2, max_lag)
        
        assert False  # RED phase - expected to fail


class TestHandlesInsufficientObservations:
    """Test that the service handles insufficient observations with appropriate error"""
    
    def test_data_shorter_than_max_lag(self):
        """Test error when data length is less than max_lag"""
        from lag_analysis_service import LagService
        
        service = LagService()
        data1 = pd.Series([1, 2, 3])
        data2 = pd.Series([2, 3, 4])
        max_lag = 5  # Longer than data
        
        with pytest.raises(ValueError, match="insufficient.*observations"):
            service.calculate_lag_curve(data1, data2, max_lag)
        
        assert False  # RED phase - expected to fail
    
    def test_minimum_data_requirements(self):
        """Test minimum data length requirements"""
        from lag_analysis_service import LagService
        
        service = LagService()
        # Too few observations for correlation
        data1 = pd.Series([1])
        data2 = pd.Series([2])
        max_lag = 0
        
        with pytest.raises(ValueError, match="insufficient.*observations"):
            service.calculate_lag_curve(data1, data2, max_lag)
        
        assert False  # RED phase - expected to fail
    
    def test_unequal_length_series(self):
        """Test error when data series have different lengths"""
        from lag_analysis_service import LagService
        
        service = LagService()
        data1 = pd.Series([1, 2, 3, 4, 5])
        data2 = pd.Series([2, 3, 4])  # Shorter
        max_lag = 2
        
        with pytest.raises(ValueError, match="length|equal"):
            service.calculate_lag_curve(data1, data2, max_lag)
        
        assert False  # RED phase - expected to fail


class TestLagServiceImportsLaggedCorrelationAnalyzer:
    """Test that LagService imports and uses LaggedCorrelationAnalyzer from LAYER-CA-002-01-05"""
    
    def test_imports_lagged_correlation_analyzer(self):
        """Test that LagService imports LaggedCorrelationAnalyzer"""
        from lag_analysis_service import LagService
        
        # Check that the service has reference to LaggedCorrelationAnalyzer
        assert hasattr(LagService, '__init__')
        service = LagService()
        assert hasattr(service, 'analyzer') or hasattr(service, '_analyzer')
        
        # Verify it's from the correct module
        import inspect
        source = inspect.getsource(LagService)
        assert 'LaggedCorrelationAnalyzer' in source
        assert 'LAYER-CA-002-01-05' in source or 'layer_ca_002_01_05' in source
        
        assert False  # RED phase - expected to fail
    
    def test_uses_lagged_correlation_analyzer_methods(self):
        """Test that LagService uses LaggedCorrelationAnalyzer methods"""
        from lag_analysis_service import LagService
        
        with unittest.mock.patch('lag_analysis_service.LaggedCorrelationAnalyzer') as mock_analyzer:
            service = LagService()
            data1 = pd.Series([1, 2, 3, 4, 5])
            data2 = pd.Series([2, 3, 4, 5, 6])
            
            service.calculate_lag_curve(data1, data2, max_lag=2)
            
            # Verify analyzer was instantiated and used
            mock_analyzer.assert_called()
            mock_analyzer.return_value.calculate_lagged_correlation.assert_called()
        
        assert False  # RED phase - expected to fail
    
    def test_analyzer_integration(self):
        """Test integration between LagService and LaggedCorrelationAnalyzer"""
        from lag_analysis_service import LagService
        
        service = LagService()
        data1 = pd.Series(range(10))
        data2 = pd.Series(range(1, 11))
        
        # Should use analyzer internally
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1, data2, max_lag=3)
        
        # Verify analyzer was properly used by checking results
        assert isinstance(correlations, (list, np.ndarray))
        assert all(isinstance(c, (int, float)) for c in correlations)
        
        assert False  # RED phase - expected to fail


@pytest.mark.integration
class TestLagAnalysisIntegration:
    """Integration tests for lag analysis service with correlation analyzer"""
    
    def test_lag_service_with_correlation_analyzer(self):
        """Test LagService integration with LaggedCorrelationAnalyzer"""
        from lag_analysis_service import LagService
        from layer_ca_002_01_05 import LaggedCorrelationAnalyzer
        
        service = LagService()
        analyzer = LaggedCorrelationAnalyzer()
        
        # Create test data
        data1 = pd.Series(np.sin(np.linspace(0, 4*np.pi, 100)))
        data2 = pd.Series(np.sin(np.linspace(0.5, 4.5*np.pi, 100)))  # Shifted sine wave
        
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1, data2, max_lag=10)
        
        # Verify integration produces valid results
        assert len(lag_days) == 11
        assert len(correlations) == 11
        assert 0 <= optimal_lag <= 10
        
        assert False  # RED phase - expected to fail
    
    def test_error_propagation_from_analyzer(self):
        """Test that errors from analyzer are properly handled"""
        from lag_analysis_service import LagService
        
        service = LagService()
        
        # Test with invalid data that should cause analyzer to fail
        data1 = pd.Series([np.nan] * 10)
        data2 = pd.Series([1] * 10)
        
        with pytest.raises(ValueError):
            service.calculate_lag_curve(data1, data2, max_lag=5)
        
        assert False  # RED phase - expected to fail
    
    def test_multiple_lag_calculations(self):
        """Test multiple consecutive lag calculations"""
        from lag_analysis_service import LagService
        
        service = LagService()
        
        # Multiple datasets
        datasets = [
            (pd.Series(range(20)), pd.Series(range(2, 22))),
            (pd.Series(np.random.randn(50)), pd.Series(np.random.randn(50))),
            (pd.Series(np.sin(np.linspace(0, 2*np.pi, 30))), pd.Series(np.cos(np.linspace(0, 2*np.pi, 30))))
        ]
        
        results = []
        for data1, data2 in datasets:
            lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1, data2, max_lag=5)
            results.append((lag_days, correlations, optimal_lag))
        
        # Verify all calculations completed
        assert len(results) == 3
        for lag_days, correlations, optimal_lag in results:
            assert len(lag_days) == 6
            assert len(correlations) == 6
            assert isinstance(optimal_lag, int)
        
        assert False  # RED phase - expected to fail


@pytest.mark.integration
class TestLagAnalysisWithDataPreprocessing:
    """Integration tests for lag analysis with data preprocessing"""
    
    def test_lag_analysis_with_normalization(self):
        """Test lag analysis with normalized data"""
        from lag_analysis_service import LagService
        
        service = LagService()
        
        # Create data with different scales
        data1 = pd.Series(np.random.randn(100) * 1000 + 5000)
        data2 = pd.Series(np.random.randn(100) * 0.1 + 0.5)
        
        # Normalize data
        data1_norm = (data1 - data1.mean()) / data1.std()
        data2_norm = (data2 - data2.mean()) / data2.std()
        
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1_norm, data2_norm, max_lag=10)
        
        assert all(-1 <= c <= 1 for c in correlations)
        assert False  # RED phase - expected to fail
    
    def test_lag_analysis_with_missing_data_handling(self):
        """Test lag analysis after handling missing data"""
        from lag_analysis_service import LagService
        
        service = LagService()
        
        # Create data with some missing values
        data1 = pd.Series([1, 2, np.nan, 4, 5, 6, np.nan, 8, 9, 10])
        data2 = pd.Series([2, 3, 4, np.nan, 6, 7, 8, 9, np.nan, 11])
        
        # Fill missing values
        data1_filled = data1.fillna(method='ffill')
        data2_filled = data2.fillna(method='ffill')
        
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1_filled, data2_filled, max_lag=3)
        
        assert len(correlations) == 4
        assert not any(np.isnan(correlations))
        
        assert False  # RED phase - expected to fail
    
    def test_lag_analysis_with_outlier_removal(self):
        """Test lag analysis after outlier removal"""
        from lag_analysis_service import LagService
        
        service = LagService()
        
        # Create data with outliers
        np.random.seed(42)
        data1 = pd.Series(np.random.randn(100))
        data1[50] = 100  # Add outlier
        
        data2 = pd.Series(np.random.randn(100))
        data2[75] = -100  # Add outlier
        
        # Remove outliers (values beyond 3 standard deviations)
        def remove_outliers(series):
            z_scores = np.abs((series - series.mean()) / series.std())
            return series[z_scores < 3]
        
        data1_clean = remove_outliers(data1)
        data2_clean = remove_outliers(data2)
        
        # Ensure equal length
        min_len = min(len(data1_clean), len(data2_clean))
        data1_clean = data1_clean[:min_len]
        data2_clean = data2_clean[:min_len]
        
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1_clean, data2_clean, max_lag=5)
        
        assert len(lag_days) == 6
        assert False  # RED phase - expected to fail


@pytest.mark.e2e
class TestLagAnalysisEndToEnd:
    """End-to-end tests for complete lag analysis workflow"""
    
    def test_complete_lag_analysis_workflow(self):
        """Test complete workflow from raw data to lag analysis results"""
        from lag_analysis_service import LagService
        
        # Simulate loading data from file
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        temperature = pd.Series(20 + 10 * np.sin(np.linspace(0, 4*np.pi, 100)) + np.random.randn(100), index=dates)
        sales = pd.Series(1000 + 500 * np.sin(np.linspace(0.5, 4.5*np.pi, 100)) + 50 * np.random.randn(100), index=dates)
        
        # Create service
        service = LagService()
        
        # Perform lag analysis
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(temperature, sales, max_lag=14)
        
        # Verify complete results
        assert len(lag_days) == 15
        assert len(correlations) == 15
        assert 0 <= optimal_lag <= 14
        assert all(isinstance(c, (int, float)) for c in correlations)
        assert all(-1 <= c <= 1 for c in correlations)
        
        # Verify optimal lag makes sense
        assert correlations[optimal_lag] == max(correlations, key=abs)
        
        assert False  # RED phase - expected to fail
    
    def test_lag_analysis_with_real_world_constraints(self):
        """Test lag analysis with real-world data constraints"""
        from lag_analysis_service import LagService
        
        service = LagService()
        
        # Simulate real-world financial data
        np.random.seed(123)
        n_points = 252  # One year of trading days
        
        # Market index with trend and volatility
        market_index = pd.Series(
            100 * np.exp(np.cumsum(0.0005 + 0.01 * np.random.randn(n_points)))
        )
        
        # Stock price with lagged response to market
        lag = 3
        stock_price = pd.Series(
            50 * np.exp(np.cumsum(0.0003 + 0.015 * np.random.randn(n_points)))
        )
        stock_price[lag:] = stock_price[lag:].values * (1 + 0.5 * market_index[:-lag].pct_change().fillna(0).values)
        
        # Analyze lag
        lag_days, correlations, optimal_lag = service.calculate_lag_curve(market_index, stock_price, max_lag=10)
        
        # Verify results match expected lag
        assert optimal_lag >= 2 and optimal_lag <= 4  # Should detect lag around 3
        assert correlations[optimal_lag] > 0.5  # Should show positive correlation
        
        assert False  # RED phase - expected to fail
    
    def test_batch_lag_analysis_processing(self):
        """Test processing multiple lag analyses in batch"""
        from lag_analysis_service import LagService
        
        service = LagService()
        
        # Create multiple pairs of time series
        n_pairs = 5
        n_points = 200
        results = []
        
        for i in range(n_pairs):
            # Generate correlated time series with different lags
            np.random.seed(i)
            base_signal = np.sin(np.linspace(0, 6*np.pi, n_points)) + 0.1 * np.random.randn(n_points)
            
            # Create lagged version
            lag = i * 2  # Different lag for each pair
            lagged_signal = np.zeros(n_points)
            lagged_signal[lag:] = base_signal[:-lag] if lag > 0 else base_signal
            lagged_signal += 0.1 * np.random.randn(n_points)  # Add noise
            
            data1 = pd.Series(base_signal)
            data2 = pd.Series(lagged_signal)
            
            # Calculate lag curve
            lag_days, correlations, optimal_lag = service.calculate_lag_curve(data1, data2, max_lag=15)
            
            results.append({
                'pair_id': i,
                'expected_lag': lag,
                'detected_lag': optimal_lag,
                'max_correlation': correlations[optimal_lag],
                'lag_days': lag_days,
                'correlations': correlations
            })
        
        # Verify all analyses completed
        assert len(results) == n_pairs
        
        # Verify lag detection accuracy
        for result in results:
            if result['expected_lag'] <= 10:  # Within analysis range
                assert abs(result['detected_lag'] - result['expected_lag']) <= 2
        
        assert False  # RED phase - expected to fail