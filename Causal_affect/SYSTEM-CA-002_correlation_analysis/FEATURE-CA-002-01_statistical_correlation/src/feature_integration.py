"""
Feature Integration Module for Statistical Correlation Calculator
Feature ID: FEATURE-CA-002-01

This module orchestrates the various correlation calculation layers to provide
a unified interface for statistical correlation analysis.
"""

from pathlib import Path
import sys
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import layer implementations
from LAYER_CA_002_01_01_pearson_calculator.src.implementation import PearsonCalculator
from LAYER_CA_002_01_02_spearman_calculator.src.implementation import (
    CorrelationMethod, 
    CorrelationResult, 
    SpearmanCalculator
)
from LAYER_CA_002_01_03_kendall_calculator.src.implementation import (
    KendallCalculator, 
    KendallFeature
)
from LAYER_CA_002_01_04_partial_correlation.src.implementation import (
    PartialCorrelationResult, 
    PartialCorrelationAnalyzer
)
from LAYER_CA_002_01_05_lagged_correlation.src.implementation import (
    LaggedCorrelationResult, 
    LaggedCorrelationAnalyzer
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CorrelationType(Enum):
    """Enumeration of available correlation types."""
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"
    PARTIAL = "partial"
    LAGGED = "lagged"


@dataclass
class FeatureConfig:
    """Configuration for the Statistical Correlation Calculator feature."""
    enable_pearson: bool = True
    enable_spearman: bool = True
    enable_kendall: bool = True
    enable_partial: bool = True
    enable_lagged: bool = True
    default_lag_range: Tuple[int, int] = (1, 10)
    significance_level: float = 0.05
    verbose: bool = False


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations."""
    success: bool
    correlation_type: Optional[CorrelationType] = None
    results: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeatureOrchestrator:
    """
    Main orchestrator for the Statistical Correlation Calculator feature.
    
    This class coordinates all correlation calculation layers and provides
    a unified interface for statistical correlation analysis.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the FeatureOrchestrator with given configuration.
        
        Args:
            config: Feature configuration. If None, uses default configuration.
        """
        self.config = config or FeatureConfig()
        self._initialize_layers()
        
    def _initialize_layers(self) -> None:
        """Initialize all correlation calculator layers."""
        try:
            if self.config.enable_pearson:
                self.pearson_calculator = PearsonCalculator()
                logger.info("Pearson calculator initialized successfully")
                
            if self.config.enable_spearman:
                self.spearman_calculator = SpearmanCalculator()
                logger.info("Spearman calculator initialized successfully")
                
            if self.config.enable_kendall:
                self.kendall_calculator = KendallCalculator()
                self.kendall_feature = KendallFeature()
                logger.info("Kendall calculator initialized successfully")
                
            if self.config.enable_partial:
                self.partial_analyzer = PartialCorrelationAnalyzer()
                logger.info("Partial correlation analyzer initialized successfully")
                
            if self.config.enable_lagged:
                self.lagged_analyzer = LaggedCorrelationAnalyzer()
                logger.info("Lagged correlation analyzer initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing layers: {str(e)}")
            raise RuntimeError(f"Failed to initialize correlation layers: {str(e)}")
    
    def calculate_correlation(
        self,
        data: Union[np.ndarray, pd.DataFrame],
        method: Union[str, CorrelationType],
        **kwargs
    ) -> FeatureResponse:
        """
        Calculate correlation using the specified method.
        
        Args:
            data: Input data as numpy array or pandas DataFrame
            method: Correlation method to use
            **kwargs: Additional method-specific parameters
            
        Returns:
            FeatureResponse containing calculation results
        """
        try:
            # Convert string to CorrelationType if necessary
            if isinstance(method, str):
                method = CorrelationType(method.lower())
                
            # Validate input data
            if not self._validate_data(data):
                return FeatureResponse(
                    success=False,
                    errors=["Invalid input data format"]
                )
            
            # Route to appropriate calculator
            if method == CorrelationType.PEARSON:
                return self._calculate_pearson(data, **kwargs)
            elif method == CorrelationType.SPEARMAN:
                return self._calculate_spearman(data, **kwargs)
            elif method == CorrelationType.KENDALL:
                return self._calculate_kendall(data, **kwargs)
            elif method == CorrelationType.PARTIAL:
                return self._calculate_partial(data, **kwargs)
            elif method == CorrelationType.LAGGED:
                return self._calculate_lagged(data, **kwargs)
            else:
                return FeatureResponse(
                    success=False,
                    errors=[f"Unsupported correlation method: {method}"]
                )
                
        except Exception as e:
            logger.error(f"Error in calculate_correlation: {str(e)}")
            return FeatureResponse(
                success=False,
                errors=[f"Calculation error: {str(e)}"]
            )
    
    def calculate_all_correlations(
        self,
        data: Union[np.ndarray, pd.DataFrame],
        **kwargs
    ) -> FeatureResponse:
        """
        Calculate all enabled correlation types for the given data.
        
        Args:
            data: Input data as numpy array or pandas DataFrame
            **kwargs: Additional parameters for specific methods
            
        Returns:
            FeatureResponse containing all correlation results
        """
        results = {}
        errors = []
        warnings = []
        
        # Calculate each enabled correlation type
        for correlation_type in CorrelationType:
            if self._is_method_enabled(correlation_type):
                response = self.calculate_correlation(data, correlation_type, **kwargs)
                if response.success:
                    results[correlation_type.value] = response.results
                else:
                    errors.extend(response.errors)
                    warnings.extend(response.warnings)
        
        return FeatureResponse(
            success=len(results) > 0,
            results=results,
            errors=errors,
            warnings=warnings,
            metadata={"methods_calculated": list(results.keys())}
        )
    
    def _calculate_pearson(self, data: Union[np.ndarray, pd.DataFrame], **kwargs) -> FeatureResponse:
        """Calculate Pearson correlation."""
        if not self.config.enable_pearson:
            return FeatureResponse(
                success=False,
                errors=["Pearson correlation is disabled"]
            )
            
        try:
            # Convert data if necessary
            if isinstance(data, pd.DataFrame):
                data_array = data.values
            else:
                data_array = data
                
            # Calculate correlation
            result = self.pearson_calculator.calculate_correlation(data_array)
            
            return FeatureResponse(
                success=True,
                correlation_type=CorrelationType.PEARSON,
                results={
                    "correlation_matrix": result,
                    "method": "pearson"
                },
                metadata={"shape": result.shape if hasattr(result, 'shape') else None}
            )
            
        except Exception as e:
            logger.error(f"Error in Pearson calculation: {str(e)}")
            return FeatureResponse(
                success=False,
                correlation_type=CorrelationType.PEARSON,
                errors=[f"Pearson calculation failed: {str(e)}"]
            )
    
    def _calculate_spearman(self, data: Union[np.ndarray, pd.DataFrame], **kwargs) -> FeatureResponse:
        """Calculate Spearman correlation."""
        if not self.config.enable_spearman:
            return FeatureResponse(
                success=False,
                errors=["Spearman correlation is disabled"]
            )
            
        try:
            # The Spearman calculator might return a CorrelationResult object
            result = self.spearman_calculator.calculate_correlation(data)
            
            # Extract results based on the implementation
            if isinstance(result, CorrelationResult):
                results_dict = {
                    "correlation_matrix": result.correlation_matrix,
                    "p_values": result.p_values if hasattr(result, 'p_values') else None,
                    "method": "spearman"
                }
            else:
                results_dict = {
                    "correlation_matrix": result,
                    "method": "spearman"
                }
            
            return FeatureResponse(
                success=True,
                correlation_type=CorrelationType.SPEARMAN,
                results=results_dict
            )
            
        except Exception as e:
            logger.error(f"Error in Spearman calculation: {str(e)}")
            return FeatureResponse(
                success=False,
                correlation_type=CorrelationType.SPEARMAN,
                errors=[f"Spearman calculation failed: {str(e)}"]
            )
    
    def _calculate_kendall(self, data: Union[np.ndarray, pd.DataFrame], **kwargs) -> FeatureResponse:
        """Calculate Kendall correlation."""
        if not self.config.enable_kendall:
            return FeatureResponse(
                success=False,
                errors=["Kendall correlation is disabled"]
            )
            
        try:
            # Use KendallCalculator for calculation
            result = self.kendall_calculator.calculate_correlation(data)
            
            return FeatureResponse(
                success=True,
                correlation_type=CorrelationType.KENDALL,
                results={
                    "correlation_matrix": result,
                    "method": "kendall"
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Kendall calculation: {str(e)}")
            return FeatureResponse(
                success=False,
                correlation_type=CorrelationType.KENDALL,
                errors=[f"Kendall calculation failed: {str(e)}"]
            )
    
    def _calculate_partial(
        self,
        data: Union[np.ndarray, pd.DataFrame],
        control_variables: Optional[List[int]] = None,
        **kwargs
    ) -> FeatureResponse:
        """Calculate partial correlation."""
        if not self.config.enable_partial:
            return FeatureResponse(
                success=False,
                errors=["Partial correlation is disabled"]
            )
            
        try:
            # Partial correlation requires control variables
            if control_variables is None:
                return FeatureResponse(
                    success=False,
                    correlation_type=CorrelationType.PARTIAL,
                    errors=["Control variables must be specified for partial correlation"]
                )
            
            result = self.partial_analyzer.calculate_partial_correlation(
                data, control_variables, **kwargs
            )
            
            # Handle PartialCorrelationResult
            if isinstance(result, PartialCorrelationResult):
                results_dict = {
                    "correlation_matrix": result.partial_correlation_matrix,
                    "p_values": result.p_values if hasattr(result, 'p_values') else None,
                    "control_variables": control_variables,
                    "method": "partial"
                }
            else:
                results_dict = {
                    "correlation_matrix": result,
                    "control_variables": control_variables,
                    "method": "partial"
                }
            
            return FeatureResponse(
                success=True,
                correlation_type=CorrelationType.PARTIAL,
                results=results_dict
            )
            
        except Exception as e:
            logger.error(f"Error in partial correlation calculation: {str(e)}")
            return FeatureResponse(
                success=False,
                correlation_type=CorrelationType.PARTIAL,
                errors=[f"Partial correlation calculation failed: {str(e)}"]
            )
    
    def _calculate_lagged(
        self,
        data: Union[np.ndarray, pd.DataFrame],
        max_lag: Optional[int] = None,
        **kwargs
    ) -> FeatureResponse:
        """Calculate lagged correlation."""
        if not self.config.enable_lagged:
            return FeatureResponse(
                success=False,
                errors=["Lagged correlation is disabled"]
            )
            
        try:
            # Use default lag range if not specified
            if max_lag is None:
                max_lag = self.config.default_lag_range[1]
            
            result = self.lagged_analyzer.calculate_lagged_correlation(
                data, max_lag=max_lag, **kwargs
            )
            
            # Handle LaggedCorrelationResult
            if isinstance(result, LaggedCorrelationResult):
                results_dict = {
                    "lagged_correlations": result.lagged_correlations,
                    "optimal_lag": result.optimal_lag if hasattr(result, 'optimal_lag') else None,
                    "max_lag": max_lag,
                    "method": "lagged"
                }
            else:
                results_dict = {
                    "lagged_correlations": result,
                    "max_lag": max_lag,
                    "method": "lagged"
                }
            
            return FeatureResponse(
                success=True,
                correlation_type=CorrelationType.LAGGED,
                results=results_dict
            )
            
        except Exception as e:
            logger.error(f"Error in lagged correlation calculation: {str(e)}")
            return FeatureResponse(
                success=False,
                correlation_type=CorrelationType.LAGGED,
                errors=[f"Lagged correlation calculation failed: {str(e)}"]
            )
    
    def _validate_data(self, data: Union[np.ndarray, pd.DataFrame]) -> bool:
        """
        Validate input data for correlation calculation.
        
        Args:
            data: Input data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if isinstance(data, pd.DataFrame):
                # Check if DataFrame has numeric data
                if not data.select_dtypes(include=[np.number]).empty:
                    return True
            elif isinstance(data, np.ndarray):
                # Check if array is numeric and has appropriate dimensions
                if np.issubdtype(data.dtype, np.number) and data.ndim >= 1:
                    return True
            return False
        except Exception:
            return False
    
    def _is_method_enabled(self, method: CorrelationType) -> bool:
        """Check if a correlation method is enabled in configuration."""
        method_config_map = {
            CorrelationType.PEARSON: self.config.enable_pearson,
            CorrelationType.SPEARMAN: self.config.enable_spearman,
            CorrelationType.KENDALL: self.config.enable_kendall,
            CorrelationType.PARTIAL: self.config.enable_partial,
            CorrelationType.LAGGED: self.config.enable_lagged
        }
        return method_config_map.get(method, False)
    
    def get_available_methods(self) -> List[str]:
        """
        Get list of available correlation methods based on configuration.
        
        Returns:
            List of available method names
        """
        available = []
        for method in CorrelationType:
            if self._is_method_enabled(method):
                available.append(method.value)
        return available