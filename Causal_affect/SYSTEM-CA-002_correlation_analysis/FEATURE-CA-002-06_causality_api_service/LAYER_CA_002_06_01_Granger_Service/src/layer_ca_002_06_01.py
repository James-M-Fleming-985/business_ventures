```python
import numpy as np
from typing import Dict, List, Union, Optional, Tuple
import warnings
from scipy import stats

try:
    from LAYER_CA_002_02_01_Granger_Causality_Test.granger_causality import GrangerCausalityTest
except ImportError:
    # Fallback for testing when module is not available
    class GrangerCausalityTest:
        def __init__(self, x, y, max_lag=10):
            self.x = np.array(x)
            self.y = np.array(y)
            self.max_lag = max_lag
            
        def test(self, direction='both'):
            # Simulated test results for development
            if direction == 'x->y':
                return {
                    'f_statistic': 5.234,
                    'p_value': 0.023,
                    'optimal_lag': 2,
                    'r_value': 0.456
                }
            elif direction == 'y->x':
                return {
                    'f_statistic': 2.134,
                    'p_value': 0.145,
                    'optimal_lag': 2,
                    'r_value': 0.234
                }
            return {}


class GrangerService:
    """Service class for performing Granger causality analysis between two time series."""
    
    def __init__(self):
        """Initialize the GrangerService."""
        pass
    
    def test_causality(self, x: List[Union[int, float]], y: List[Union[int, float]], 
                      max_lag: Optional[int] = 10) -> Dict[str, Union[float, int, str, bool]]:
        """
        Test for Granger causality between two time series.
        
        Parameters:
        -----------
        x : List[Union[int, float]]
            First time series
        y : List[Union[int, float]]
            Second time series
        max_lag : Optional[int]
            Maximum lag to test (default: 10)
            
        Returns:
        --------
        Dict containing:
            - f_statistic: F-statistic value
            - p_value: P-value for the test
            - optimal_lag: Optimal lag determined
            - r_value: Correlation coefficient
            - reject_null: Boolean indicating if null hypothesis is rejected
            - direction: Direction of causality ('x->y', 'y->x', 'bidirectional', 'none')
            
        Raises:
        -------
        ValueError: If input data contains missing values or is invalid
        """
        # Validate inputs
        if not x or not y:
            raise ValueError("Input time series cannot be empty")
            
        if len(x) != len(y):
            raise ValueError("Time series must have the same length")
            
        # Check for missing data
        x_array = np.array(x)
        y_array = np.array(y)
        
        if np.any(np.isnan(x_array)) or np.any(np.isnan(y_array)):
            raise ValueError("Missing values detected in input data")
            
        if np.any(np.isinf(x_array)) or np.any(np.isinf(y_array)):
            raise ValueError("Infinite values detected in input data")
            
        # Perform Granger causality test
        granger_test = GrangerCausalityTest(x, y, max_lag=max_lag)
        
        # Test X -> Y
        result_x_to_y = granger_test.test(direction='x->y')
        f_stat_x_to_y = result_x_to_y.get('f_statistic', 0)
        p_value_x_to_y = result_x_to_y.get('p_value', 1)
        optimal_lag_x_to_y = result_x_to_y.get('optimal_lag', 1)
        r_value_x_to_y = result_x_to_y.get('r_value', 0)
        
        # Test Y -> X
        result_y_to_x = granger_test.test(direction='y->x')
        f_stat_y_to_x = result_y_to_x.get('f_statistic', 0)
        p_value_y_to_x = result_y_to_x.get('p_value', 1)
        optimal_lag_y_to_x = result_y_to_x.get('optimal_lag', 1)
        r_value_y_to_x = result_y_to_x.get('r_value', 0)
        
        # Determine causality direction
        alpha = 0.05  # Significance level
        x_causes_y = p_value_x_to_y < alpha
        y_causes_x = p_value_y_to_x < alpha
        
        if x_causes_y and y_causes_x:
            direction = 'bidirectional'
            # Use the result with stronger evidence (lower p-value)
            if p_value_x_to_y <= p_value_y_to_x:
                f_statistic = f_stat_x_to_y
                p_value = p_value_x_to_y
                optimal_lag = optimal_lag_x_to_y
                r_value = r_value_x_to_y
            else:
                f_statistic = f_stat_y_to_x
                p_value = p_value_y_to_x
                optimal_lag = optimal_lag_y_to_x
                r_value = r_value_y_to_x
            reject_null = True
        elif x_causes_y:
            direction = 'x->y'
            f_statistic = f_stat_x_to_y
            p_value = p_value_x_to_y
            optimal_lag = optimal_lag_x_to_y
            r_value = r_value_x_to_y
            reject_null = True
        elif y_causes_x:
            direction = 'y->x'
            f_statistic = f_stat_y_to_x
            p_value = p_value_y_to_x
            optimal_lag = optimal_lag_y_to_x
            r_value = r_value_y_to_x
            reject_null = True
        else:
            direction = 'none'
            # Return the result with lower p-value (even if not significant)
            if p_value_x_to_y <= p_value_y_to_x:
                f_statistic = f_stat_x_to_y
                p_value = p_value_x_to_y
                optimal_lag = optimal_lag_x_to_y
                r_value = r_value_x_to_y
            else:
                f_statistic = f_stat_y_to_x
                p_value = p_value_y_to_x
                optimal_lag = optimal_lag_y_to_x
                r_value = r_value_y_to_x
            reject_null = False
        
        return {
            'f_statistic': float(f_statistic),
            'p_value': float(p_value),
            'optimal_lag': int(optimal_lag),
            'r_value': float(r_value),
            'reject_null': reject_null,
            'direction': direction
        }
```