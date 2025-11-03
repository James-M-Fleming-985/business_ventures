```python
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import pandas as pd
from scipy import stats


class CorrelationExplanation:
    """Provides explanations for correlation analysis results."""
    
    def __init__(self):
        """Initialize the CorrelationExplanation instance."""
        self.explanation_templates = {
            'strong_positive': "There is a strong positive correlation (r={r:.3f}) between {var1} and {var2}. "
                              "This means that as {var1} increases, {var2} tends to increase as well.",
            'strong_negative': "There is a strong negative correlation (r={r:.3f}) between {var1} and {var2}. "
                              "This means that as {var1} increases, {var2} tends to decrease.",
            'moderate_positive': "There is a moderate positive correlation (r={r:.3f}) between {var1} and {var2}. "
                                "This suggests a tendency for {var2} to increase as {var1} increases.",
            'moderate_negative': "There is a moderate negative correlation (r={r:.3f}) between {var1} and {var2}. "
                                "This suggests a tendency for {var2} to decrease as {var1} increases.",
            'weak_positive': "There is a weak positive correlation (r={r:.3f}) between {var1} and {var2}. "
                            "The relationship is minimal but slightly positive.",
            'weak_negative': "There is a weak negative correlation (r={r:.3f}) between {var1} and {var2}. "
                            "The relationship is minimal but slightly negative.",
            'no_correlation': "There is no significant correlation (r={r:.3f}) between {var1} and {var2}. "
                             "The variables appear to be independent of each other."
        }
    
    def explain_correlation(self, correlation: float, var1: str, var2: str, 
                          p_value: Optional[float] = None) -> str:
        """
        Generate an explanation for a correlation value.
        
        Args:
            correlation: The correlation coefficient (-1 to 1)
            var1: Name of the first variable
            var2: Name of the second variable
            p_value: Optional p-value for statistical significance
            
        Returns:
            A human-readable explanation of the correlation
        """
        if not -1 <= correlation <= 1:
            raise ValueError("Correlation must be between -1 and 1")
        
        # Determine correlation strength and direction
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            strength = 'strong'
        elif abs_corr >= 0.3:
            strength = 'moderate'
        elif abs_corr >= 0.1:
            strength = 'weak'
        else:
            return self.explanation_templates['no_correlation'].format(
                r=correlation, var1=var1, var2=var2
            )
        
        direction = 'positive' if correlation > 0 else 'negative'
        template_key = f"{strength}_{direction}"
        
        explanation = self.explanation_templates[template_key].format(
            r=correlation, var1=var1, var2=var2
        )
        
        # Add p-value information if provided
        if p_value is not None:
            if p_value < 0.05:
                explanation += f" This correlation is statistically significant (p={p_value:.4f})."
            else:
                explanation += f" This correlation is not statistically significant (p={p_value:.4f})."
        
        return explanation
    
    def explain_correlation_matrix(self, correlation_matrix: Union[np.ndarray, pd.DataFrame],
                                 variable_names: Optional[List[str]] = None,
                                 p_values: Optional[Union[np.ndarray, pd.DataFrame]] = None) -> Dict[str, str]:
        """
        Generate explanations for all correlations in a correlation matrix.
        
        Args:
            correlation_matrix: Square correlation matrix
            variable_names: Names of variables (if not provided in DataFrame)
            p_values: Optional matrix of p-values
            
        Returns:
            Dictionary mapping variable pairs to explanations
        """
        # Convert to numpy array if pandas DataFrame
        if isinstance(correlation_matrix, pd.DataFrame):
            if variable_names is None:
                variable_names = list(correlation_matrix.columns)
            corr_array = correlation_matrix.values
        else:
            corr_array = correlation_matrix
            
        # Validate inputs
        if corr_array.shape[0] != corr_array.shape[1]:
            raise ValueError("Correlation matrix must be square")
        
        n_vars = corr_array.shape[0]
        
        if variable_names is None:
            variable_names = [f"Variable_{i+1}" for i in range(n_vars)]
        elif len(variable_names) != n_vars:
            raise ValueError("Number of variable names must match matrix dimensions")
        
        # Convert p_values to numpy array if pandas DataFrame
        if isinstance(p_values, pd.DataFrame):
            p_values = p_values.values
        
        # Generate explanations for each pair
        explanations = {}
        for i in range(n_vars):
            for j in range(i+1, n_vars):
                pair_key = f"{variable_names[i]}_{variable_names[j]}"
                p_val = None
                if p_values is not None:
                    p_val = p_values[i, j]
                
                explanations[pair_key] = self.explain_correlation(
                    corr_array[i, j],
                    variable_names[i],
                    variable_names[j],
                    p_val
                )
        
        return explanations
    
    def get_key_findings(self, correlation_matrix: Union[np.ndarray, pd.DataFrame],
                        variable_names: Optional[List[str]] = None,
                        threshold: float = 0.5) -> List[str]:
        """
        Extract key findings from a correlation matrix.
        
        Args:
            correlation_matrix: Square correlation matrix
            variable_names: Names of variables
            threshold: Minimum absolute correlation to be considered a key finding
            
        Returns:
            List of key findings as strings
        """
        # Convert to numpy array if pandas DataFrame
        if isinstance(correlation_matrix, pd.DataFrame):
            if variable_names is None:
                variable_names = list(correlation_matrix.columns)
            corr_array = correlation_matrix.values
        else:
            corr_array = correlation_matrix
        
        n_vars = corr_array.shape[0]
        
        if variable_names is None:
            variable_names = [f"Variable_{i+1}" for i in range(n_vars)]
        
        findings = []
        
        # Find strong correlations
        for i in range(n_vars):
            for j in range(i+1, n_vars):
                corr = corr_array[i, j]
                if abs(corr) >= threshold:
                    if corr > 0:
                        findings.append(f"Strong positive correlation between {variable_names[i]} "
                                      f"and {variable_names[j]} (r={corr:.3f})")
                    else:
                        findings.append(f"Strong negative correlation between {variable_names[i]} "
                                      f"and {variable_names[j]} (r={corr:.3f})")
        
        # Add summary if no strong correlations found
        if not findings:
            findings.append("No strong correlations found above the threshold.")
        
        return findings
    
    def suggest_further_analysis(self, correlation: float, var1: str, var2: str) -> List[str]:
        """
        Suggest further analyses based on correlation results.
        
        Args:
            correlation: The correlation coefficient
            var1: Name of the first variable
            var2: Name of the second variable
            
        Returns:
            List of suggested analyses
        """
        suggestions = []
        abs_corr = abs(correlation)
        
        if abs_corr >= 0.7:
            suggestions.append(f"Consider regression analysis to model the relationship between {var1} and {var2}")
            suggestions.append("Check for potential confounding variables that might explain this strong correlation")
            suggestions.append("Investigate whether there is a causal relationship or just association")
        elif abs_corr >= 0.3:
            suggestions.append(f"Explore scatter plots to visualize the relationship between {var1} and {var2}")
            suggestions.append("Consider partial correlation analysis to control for other variables")
            suggestions.append("Check for non-linear relationships that might be missed by correlation")
        else:
            suggestions.append(f"The weak correlation between {var1} and {var2} suggests exploring other variables")
            suggestions.append("Consider whether the relationship might be non-linear")
            suggestions.append("Check if subgroups in your data show different correlation patterns")
        
        # General suggestions
        suggestions.append("Ensure data quality and check for outliers that might affect the correlation")
        
        return suggestions


def explain_correlation_strength(correlation: float) -> str:
    """
    Provide a simple explanation of correlation strength.
    
    Args:
        correlation: The correlation coefficient
        
    Returns:
        Description of correlation strength
    """
    abs_corr = abs(correlation)
    
    if abs_corr >= 0.9:
        return "very strong"
    elif abs_corr >= 0.7:
        return "strong"
    elif abs_corr >= 0.5:
        return "moderate"
    elif abs_corr >= 0.3:
        return "weak"
    elif abs_corr >= 0.1:
        return "very weak"
    else:
        return "negligible"


def format_correlation_report(correlations: Dict[Tuple[str, str], float],
                            p_values: Optional[Dict[Tuple[str, str], float]] = None) -> str:
    """
    Format correlation results into a readable report.
    
    Args:
        correlations: Dictionary mapping variable pairs to correlation values
        p_values: Optional dictionary mapping variable pairs to p-values
        
    Returns:
        Formatted report as string
    """
    report_lines = ["Correlation Analysis Report", "=" * 30, ""]
    
    for (var1, var2), corr in correlations.items():
        strength = explain_correlation_strength(corr)
        direction = "positive" if corr > 0 else "negative"
        
        line = f"{var1} vs {var2}: r = {corr:.3f} ({strength} {direction})"
        
        if p_values and (var1, var2) in p_values:
            p_val = p_values[(var1, var2)]
            sig = "significant" if p_val < 0.05 else "not significant"
            line += f", p = {p_val:.4f} ({sig})"
        
        report_lines.append(line)
    
    return "\n".join(report_lines)
```