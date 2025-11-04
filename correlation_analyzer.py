"""
Simplified Correlation Analyzer
Performs statistical correlation analysis on real-world data
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """Analyze correlations between time series data."""
    
    @staticmethod
    def pearson_correlation(x: List[float], y: List[float]) -> Tuple[float, float]:
        """Calculate Pearson correlation coefficient and p-value."""
        try:
            corr, p_value = stats.pearsonr(x, y)
            return float(corr), float(p_value)
        except Exception as e:
            logger.error(f"Pearson correlation error: {e}")
            return 0.0, 1.0
    
    @staticmethod
    def spearman_correlation(x: List[float], y: List[float]) -> Tuple[float, float]:
        """Calculate Spearman rank correlation coefficient and p-value."""
        try:
            corr, p_value = stats.spearmanr(x, y)
            return float(corr), float(p_value)
        except Exception as e:
            logger.error(f"Spearman correlation error: {e}")
            return 0.0, 1.0
    
    @staticmethod
    def kendall_correlation(x: List[float], y: List[float]) -> Tuple[float, float]:
        """Calculate Kendall's tau correlation coefficient and p-value."""
        try:
            corr, p_value = stats.kendalltau(x, y)
            return float(corr), float(p_value)
        except Exception as e:
            logger.error(f"Kendall correlation error: {e}")
            return 0.0, 1.0
    
    def analyze_matrix(
        self,
        data: Dict[str, List[float]],
        method: str = "pearson",
        min_threshold: float = 0.3
    ) -> Dict:
        """
        Analyze correlations between all variable pairs.
        
        Args:
            data: Dictionary mapping variable names to data points
            method: Correlation method (pearson, spearman, kendall)
            min_threshold: Minimum correlation to report
            
        Returns:
            Dictionary with correlation matrix, p-values, and significant pairs
        """
        variables = list(data.keys())
        n = len(variables)
        
        # Initialize correlation and p-value matrices
        corr_matrix = np.zeros((n, n))
        p_matrix = np.zeros((n, n))
        
        # Choose correlation function
        if method == "spearman":
            corr_func = self.spearman_correlation
        elif method == "kendall":
            corr_func = self.kendall_correlation
        else:
            corr_func = self.pearson_correlation
        
        # Calculate correlations
        for i, var1 in enumerate(variables):
            for j, var2 in enumerate(variables):
                if i == j:
                    corr_matrix[i, j] = 1.0
                    p_matrix[i, j] = 0.0
                elif i < j:
                    # Only calculate upper triangle
                    corr, p_val = corr_func(data[var1], data[var2])
                    corr_matrix[i, j] = corr
                    corr_matrix[j, i] = corr
                    p_matrix[i, j] = p_val
                    p_matrix[j, i] = p_val
        
        # Find significant correlations above threshold
        significant_pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                corr = corr_matrix[i, j]
                if abs(corr) >= min_threshold:
                    significant_pairs.append({
                        "var1": variables[i],
                        "var2": variables[j],
                        "correlation": float(corr),
                        "p_value": float(p_matrix[i, j]),
                        "strength": self._classify_strength(abs(corr)),
                        "direction": "positive" if corr > 0 else "negative"
                    })
        
        # Sort by absolute correlation strength
        significant_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        return {
            "matrix": corr_matrix.tolist(),
            "p_values": p_matrix.tolist(),
            "variables": variables,
            "method": method,
            "significant_pairs": significant_pairs,
            "threshold": min_threshold,
            "total_pairs": len(significant_pairs)
        }
    
    @staticmethod
    def _classify_strength(abs_corr: float) -> str:
        """Classify correlation strength."""
        if abs_corr >= 0.8:
            return "very_strong"
        elif abs_corr >= 0.6:
            return "strong"
        elif abs_corr >= 0.4:
            return "moderate"
        elif abs_corr >= 0.2:
            return "weak"
        else:
            return "very_weak"
    
    def generate_explanation(
        self,
        correlation: float,
        var1: str,
        var2: str,
        p_value: Optional[float] = None,
        style: str = "detailed"
    ) -> str:
        """
        Generate natural language explanation of correlation.
        
        Args:
            correlation: Correlation coefficient
            var1: First variable name
            var2: Second variable name
            p_value: Statistical p-value
            style: Explanation style (simple, detailed, technical)
            
        Returns:
            Natural language explanation
        """
        abs_corr = abs(correlation)
        strength = self._classify_strength(abs_corr)
        direction = "positive" if correlation > 0 else "negative"
        
        if style == "simple":
            return self._simple_explanation(var1, var2, direction, strength)
        elif style == "technical":
            return self._technical_explanation(var1, var2, correlation, p_value, strength)
        else:
            return self._detailed_explanation(var1, var2, correlation, p_value, direction, strength)
    
    @staticmethod
    def _simple_explanation(var1: str, var2: str, direction: str, strength: str) -> str:
        """Generate simple explanation."""
        if direction == "positive":
            return f"{var1.replace('_', ' ').title()} and {var2.replace('_', ' ').title()} tend to move together ({strength.replace('_', ' ')} relationship)."
        else:
            return f"{var1.replace('_', ' ').title()} and {var2.replace('_', ' ').title()} tend to move in opposite directions ({strength.replace('_', ' ')} relationship)."
    
    @staticmethod
    def _detailed_explanation(var1: str, var2: str, correlation: float, p_value: Optional[float], direction: str, strength: str) -> str:
        """Generate detailed explanation."""
        var1_fmt = var1.replace('_', ' ').title()
        var2_fmt = var2.replace('_', ' ').title()
        
        explanation = f"Analysis reveals a {strength.replace('_', ' ')} {direction} correlation "
        explanation += f"(r = {correlation:.3f}) between {var1_fmt} and {var2_fmt}. "
        
        if direction == "positive":
            explanation += f"This means that when {var1_fmt} increases, {var2_fmt} tends to increase as well, and vice versa. "
        else:
            explanation += f"This means that when {var1_fmt} increases, {var2_fmt} tends to decrease, and vice versa. "
        
        if p_value is not None:
            if p_value < 0.001:
                explanation += "This relationship is highly statistically significant (p < 0.001), "
                explanation += "indicating very strong evidence that this correlation is not due to chance."
            elif p_value < 0.05:
                explanation += f"This relationship is statistically significant (p = {p_value:.4f}), "
                explanation += "providing good evidence that this correlation is meaningful."
            else:
                explanation += f"However, this relationship is not statistically significant (p = {p_value:.4f}), "
                explanation += "so it may be due to chance rather than a genuine relationship."
        
        return explanation
    
    @staticmethod
    def _technical_explanation(var1: str, var2: str, correlation: float, p_value: Optional[float], strength: str) -> str:
        """Generate technical explanation."""
        explanation = f"Correlation Analysis:\n"
        explanation += f"Variables: {var1} × {var2}\n"
        explanation += f"Coefficient: r = {correlation:.6f}\n"
        explanation += f"Strength: {strength.replace('_', ' ').upper()}\n"
        
        if p_value is not None:
            explanation += f"P-value: {p_value:.6f}\n"
            explanation += f"Significance: {'YES' if p_value < 0.05 else 'NO'} (α = 0.05)\n"
        
        explanation += f"Coefficient of Determination: R² = {correlation**2:.6f}\n"
        explanation += f"Variance Explained: {(correlation**2 * 100):.2f}%"
        
        return explanation
