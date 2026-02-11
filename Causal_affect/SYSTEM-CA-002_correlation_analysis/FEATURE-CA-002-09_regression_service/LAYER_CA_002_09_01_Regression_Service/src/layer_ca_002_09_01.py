import numpy as np
import pandas as pd
from statsmodels.api import OLS, add_constant
from scipy import stats


class RegressionService:
    """Service class for calculating regression analysis with lag support."""
    
    def calculate_regression(self, x_data, y_data, x_name='X', y_name='Y', lag=0):
        """
        Calculate regression analysis between two variables with optional lag.
        
        Parameters:
        -----------
        x_data : array-like
            Independent variable data
        y_data : array-like
            Dependent variable data
        x_name : str, optional
            Name of independent variable (default: 'X')
        y_name : str, optional
            Name of dependent variable (default: 'Y')
        lag : int, optional
            Number of periods to lag x_data (default: 0)
            
        Returns:
        --------
        dict
            Dictionary containing regression results:
            - beta_0: intercept
            - beta_1: slope coefficient
            - r_squared: R-squared value
            - p_value: p-value for beta_1
            - std_error: standard error of beta_1
            - confidence_interval: 95% CI for beta_1
            - formula: regression formula string
            - interpretation: text interpretation of results
            
        Raises:
        -------
        ValueError
            If insufficient data points after lag adjustment
        """
        # Convert to numpy arrays
        x_data = np.asarray(x_data)
        y_data = np.asarray(y_data)
        
        # Apply lag to x_data
        if lag > 0:
            x_lagged = x_data[:-lag]
            y_aligned = y_data[lag:]
        else:
            x_lagged = x_data
            y_aligned = y_data
            
        # Check if we have enough data points
        if len(x_lagged) < 2 or len(y_aligned) < 2:
            raise ValueError("Insufficient data points for regression analysis")
            
        # Ensure arrays have the same length
        min_len = min(len(x_lagged), len(y_aligned))
        x_lagged = x_lagged[:min_len]
        y_aligned = y_aligned[:min_len]
        
        # Add constant term for intercept
        X = add_constant(x_lagged)
        
        # Fit OLS model
        model = OLS(y_aligned, X).fit()
        
        # Extract results
        beta_0 = model.params[0]
        beta_1 = model.params[1]
        r_squared = model.rsquared
        p_value = model.pvalues[1]
        std_error = model.bse[1]
        
        # Calculate 95% confidence interval
        conf_int = model.conf_int(alpha=0.05)
        confidence_interval = (conf_int[1][0], conf_int[1][1])
        
        # Create formula string
        if lag > 0:
            formula = f"{y_name} = {beta_0:.4f} + {beta_1:.4f} * {x_name}(t-{lag})"
        else:
            formula = f"{y_name} = {beta_0:.4f} + {beta_1:.4f} * {x_name}"
            
        # Create interpretation
        if p_value < 0.05:
            significance = "statistically significant"
        else:
            significance = "not statistically significant"
            
        if beta_1 > 0:
            direction = "positive"
        else:
            direction = "negative"
            
        if lag > 0:
            lag_text = f" with a lag of {lag} period{'s' if lag > 1 else ''}"
        else:
            lag_text = ""
            
        interpretation = (f"The relationship between {x_name} and {y_name}{lag_text} is "
                         f"{significance} (p={p_value:.4f}). "
                         f"A one unit increase in {x_name} is associated with a "
                         f"{abs(beta_1):.4f} {'increase' if beta_1 > 0 else 'decrease'} in {y_name}.")
        
        return {
            'beta_0': beta_0,
            'beta_1': beta_1,
            'r_squared': r_squared,
            'p_value': p_value,
            'std_error': std_error,
            'confidence_interval': confidence_interval,
            'formula': formula,
            'interpretation': interpretation
        }