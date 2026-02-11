import pytest
import unittest.mock
import sys
import os
import subprocess
import pathlib
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock


class TestCalculateRegressionReturnsCorrectDict:
    """Test that calculate_regression returns dict with required fields"""
    
    def test_returns_dict_with_all_required_fields(self):
        """Test that returned dict contains all required fields"""
        from regression_service import calculate_regression
        
        # This should fail in RED phase
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        result = calculate_regression(x, y, 'x', 'y')
        
        required_fields = ['beta_0', 'beta_1', 'r_squared', 'p_value', 
                          'std_error', 'confidence_interval', 'formula', 'interpretation']
        
        for field in required_fields:
            assert field in result
            
    def test_all_numeric_fields_are_numbers(self):
        """Test that numeric fields contain valid numbers"""
        from regression_service import calculate_regression
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        result = calculate_regression(x, y, 'x', 'y')
        
        numeric_fields = ['beta_0', 'beta_1', 'r_squared', 'p_value', 'std_error']
        
        for field in numeric_fields:
            assert isinstance(result[field], (int, float))
            

class TestLagShiftAppliedCorrectly:
    """Test that lag shift is applied correctly so x_lagged aligns with y"""
    
    def test_lag_shift_aligns_x_with_y(self):
        """Test that x values are shifted by one period to align with y"""
        from regression_service import calculate_regression
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 20, 30, 40, 50])
        
        with patch('regression_service.sm.OLS') as mock_ols:
            mock_model = Mock()
            mock_results = Mock()
            mock_results.params = [0, 1]
            mock_results.rsquared = 0.9
            mock_results.pvalues = [0.01, 0.01]
            mock_results.bse = [0.1, 0.1]
            mock_results.conf_int.return_value = np.array([[0, 0.2], [0.8, 1.2]])
            mock_model.fit.return_value = mock_results
            mock_ols.return_value = mock_model
            
            calculate_regression(x, y, 'x', 'y')
            
            # Check that OLS was called with lagged x (excluding first y value)
            call_args = mock_ols.call_args
            assert len(call_args[0][0]) == 4  # y should be shortened by 1
            assert len(call_args[0][1]) == 4  # x should be shortened by 1
            
    def test_lag_shift_drops_first_y_value(self):
        """Test that first y value is dropped when applying lag"""
        from regression_service import calculate_regression
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([100, 20, 30, 40, 50])  # First value is different
        
        with patch('regression_service.sm.OLS') as mock_ols:
            mock_model = Mock()
            mock_results = Mock()
            mock_results.params = [0, 1]
            mock_results.rsquared = 0.9
            mock_results.pvalues = [0.01, 0.01]
            mock_results.bse = [0.1, 0.1]
            mock_results.conf_int.return_value = np.array([[0, 0.2], [0.8, 1.2]])
            mock_model.fit.return_value = mock_results
            mock_ols.return_value = mock_model
            
            calculate_regression(x, y, 'x', 'y')
            
            # Check that first y value (100) was dropped
            y_used = mock_ols.call_args[0][0]
            assert 100 not in y_used
            

class TestBeta1HasCorrectSign:
    """Test that beta_1 has correct sign for positive correlation data"""
    
    def test_positive_correlation_yields_positive_beta1(self):
        """Test that positive correlation data produces positive beta_1"""
        from regression_service import calculate_regression
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])  # Perfect positive correlation
        
        result = calculate_regression(x, y, 'x', 'y')
        
        assert result['beta_1'] > 0
        
    def test_negative_correlation_yields_negative_beta1(self):
        """Test that negative correlation data produces negative beta_1"""
        from regression_service import calculate_regression
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])  # Perfect negative correlation
        
        result = calculate_regression(x, y, 'x', 'y')
        
        assert result['beta_1'] < 0
        

class TestRSquaredBetweenZeroAndOne:
    """Test that r_squared is between 0 and 1"""
    
    def test_r_squared_lower_bound(self):
        """Test that r_squared is not less than 0"""
        from regression_service import calculate_regression
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 1, 4, 2, 3])  # Random data
        
        result = calculate_regression(x, y, 'x', 'y')
        
        assert result['r_squared'] >= 0
        
    def test_r_squared_upper_bound(self):
        """Test that r_squared is not greater than 1"""
        from regression_service import calculate_regression
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])  # Perfect correlation
        
        result = calculate_regression(x, y, 'x', 'y')
        
        assert result['r_squared'] <= 1
        

class TestConfidenceIntervalContainsBeta1:
    """Test that confidence_interval contains beta_1 value"""
    
    def test_beta1_within_confidence_interval(self):
        """Test that beta_1 falls within its confidence interval"""
        from regression_service import calculate_regression
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        result = calculate_regression(x, y, 'x', 'y')
        
        ci_lower, ci_upper = result['confidence_interval']
        assert ci_lower <= result['beta_1'] <= ci_upper
        
    def test_confidence_interval_is_tuple(self):
        """Test that confidence_interval is a tuple with two values"""
        from regression_service import calculate_regression
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        result = calculate_regression(x, y, 'x', 'y')
        
        assert isinstance(result['confidence_interval'], tuple)
        assert len(result['confidence_interval']) == 2
        

class TestInterpretationTextFormatted:
    """Test that interpretation text is formatted correctly with variable names"""
    
    def test_interpretation_contains_variable_names(self):
        """Test that interpretation text includes both variable names"""
        from regression_service import calculate_regression
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        result = calculate_regression(x, y, 'temperature', 'sales')
        
        assert 'temperature' in result['interpretation']
        assert 'sales' in result['interpretation']
        
    def test_interpretation_mentions_beta1_value(self):
        """Test that interpretation includes the beta_1 coefficient value"""
        from regression_service import calculate_regression
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        result = calculate_regression(x, y, 'x', 'y')
        
        assert str(result['beta_1']) in result['interpretation']
        

class TestHandlesInsufficientData:
    """Test that insufficient data is handled with meaningful error message"""
    
    def test_raises_error_with_less_than_two_points(self):
        """Test that error is raised when less than 2 data points provided"""
        from regression_service import calculate_regression
        
        x = np.array([1])
        y = np.array([2])
        
        with pytest.raises(ValueError) as exc_info:
            calculate_regression(x, y, 'x', 'y')
            
        assert 'insufficient data' in str(exc_info.value).lower()
        
    def test_raises_error_with_mismatched_lengths(self):
        """Test that error is raised when x and y have different lengths"""
        from regression_service import calculate_regression
        
        x = np.array([1, 2, 3])
        y = np.array([2, 4])
        
        with pytest.raises(ValueError) as exc_info:
            calculate_regression(x, y, 'x', 'y')
            
        assert 'length' in str(exc_info.value).lower()
        

class TestUsesStatsmodelsOLS:
    """Test that statsmodels OLS is used for regression calculation"""
    
    @patch('regression_service.sm.OLS')
    def test_calls_statsmodels_ols(self, mock_ols):
        """Test that statsmodels OLS is called during calculation"""
        from regression_service import calculate_regression
        
        mock_model = Mock()
        mock_results = Mock()
        mock_results.params = [0, 1]
        mock_results.rsquared = 0.9
        mock_results.pvalues = [0.01, 0.01]
        mock_results.bse = [0.1, 0.1]
        mock_results.conf_int.return_value = np.array([[0, 0.2], [0.8, 1.2]])
        mock_model.fit.return_value = mock_results
        mock_ols.return_value = mock_model
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        calculate_regression(x, y, 'x', 'y')
        
        mock_ols.assert_called_once()
        
    @patch('regression_service.sm.add_constant')
    def test_adds_constant_for_intercept(self, mock_add_constant):
        """Test that constant is added for intercept calculation"""
        from regression_service import calculate_regression
        
        mock_add_constant.return_value = np.array([[1, 1], [1, 2], [1, 3], [1, 4]])
        
        with patch('regression_service.sm.OLS') as mock_ols:
            mock_model = Mock()
            mock_results = Mock()
            mock_results.params = [0, 1]
            mock_results.rsquared = 0.9
            mock_results.pvalues = [0.01, 0.01]
            mock_results.bse = [0.1, 0.1]
            mock_results.conf_int.return_value = np.array([[0, 0.2], [0.8, 1.2]])
            mock_model.fit.return_value = mock_results
            mock_ols.return_value = mock_model
            
            x = np.array([1, 2, 3, 4, 5])
            y = np.array([2, 4, 6, 8, 10])
            
            calculate_regression(x, y, 'x', 'y')
            
            mock_add_constant.assert_called_once()


@pytest.mark.integration
class TestRegressionServiceIntegration:
    """Integration tests for regression quantification service"""
    
    def test_regression_with_pandas_dataframe_input(self):
        """Test regression calculation with pandas DataFrame input"""
        from regression_service import calculate_regression
        
        df = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [2, 4, 6, 8, 10]
        })
        
        result = calculate_regression(df['x'].values, df['y'].values, 'x', 'y')
        
        assert isinstance(result, dict)
        assert all(key in result for key in ['beta_0', 'beta_1', 'r_squared'])
        
    def test_regression_with_real_statistical_data(self):
        """Test regression with realistic statistical data"""
        from regression_service import calculate_regression
        
        np.random.seed(42)
        x = np.random.normal(50, 10, 100)
        y = 2 * x + np.random.normal(0, 5, 100)
        
        result = calculate_regression(x, y, 'predictor', 'response')
        
        # Should find approximately beta_1 = 2
        assert 1.8 <= result['beta_1'] <= 2.2
        assert result['r_squared'] > 0.9
        
    def test_regression_pipeline_with_data_preprocessing(self):
        """Test complete regression pipeline including data preprocessing"""
        from regression_service import calculate_regression, preprocess_data
        
        # Raw data with outliers
        x = np.array([1, 2, 3, 4, 5, 100])  # 100 is an outlier
        y = np.array([2, 4, 6, 8, 10, 200])  # 200 is an outlier
        
        # Preprocess to remove outliers
        x_clean, y_clean = preprocess_data(x, y)
        
        result = calculate_regression(x_clean, y_clean, 'x', 'y')
        
        assert len(x_clean) < len(x)  # Outliers removed
        assert result['beta_1'] > 0


@pytest.mark.e2e
class TestRegressionServiceE2E:
    """End-to-end tests for regression quantification service"""
    
    def test_complete_regression_workflow(self):
        """Test complete workflow from data loading to interpretation"""
        from regression_service import RegressionService
        
        service = RegressionService()
        
        # Load test data
        data = service.load_data('test_data.csv')
        
        # Perform regression
        result = service.calculate_regression(
            data['independent'], 
            data['dependent'],
            'independent',
            'dependent'
        )
        
        # Generate report
        report = service.generate_report(result)
        
        assert 'Regression Analysis Report' in report
        assert 'R-squared' in report
        assert 'p-value' in report
        
    def test_api_endpoint_regression_calculation(self):
        """Test regression calculation through API endpoint"""
        from regression_api import app
        
        client = app.test_client()
        
        data = {
            'x': [1, 2, 3, 4, 5],
            'y': [2, 4, 6, 8, 10],
            'x_name': 'predictor',
            'y_name': 'response'
        }
        
        response = client.post('/api/regression', json=data)
        
        assert response.status_code == 200
        result = response.json
        assert 'beta_1' in result
        assert 'formula' in result
        
    def test_cli_regression_calculation(self):
        """Test regression calculation through command line interface"""
        result = subprocess.run(
            ['python', 'regression_cli.py', 
             '--x', '1,2,3,4,5',
             '--y', '2,4,6,8,10',
             '--x-name', 'temperature',
             '--y-name', 'sales'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'Regression Results' in result.stdout
        assert 'beta_1' in result.stdout
        assert 'R-squared' in result.stdout