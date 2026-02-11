"""
Feature Integration Module for Granger Causality API Service
FEATURE ID: FEATURE-CA-002-06

This module orchestrates the integration of all layers for the Granger Causality API Service.
"""

from pathlib import Path
import sys
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
import traceback
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResponseStatus(Enum):
    """Response status enumeration."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL = "partial"


@dataclass
class FeatureConfig:
    """Configuration dataclass for the Granger Causality feature."""
    max_lag: int = 10
    significance_level: float = 0.05
    test_type: str = "ssr_ftest"
    trend: str = "c"
    verbose: bool = False
    timeout_seconds: int = 300
    max_retries: int = 3
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        if self.max_lag <= 0:
            raise ValueError("max_lag must be positive")
        if not 0 < self.significance_level < 1:
            raise ValueError("significance_level must be between 0 and 1")
        if self.test_type not in ["ssr_ftest", "ssr_chi2test", "lrtest", "params_ftest"]:
            raise ValueError(f"Invalid test_type: {self.test_type}")
        if self.trend not in ["c", "ct", "ctt", "nc"]:
            raise ValueError(f"Invalid trend: {self.trend}")
        return True


@dataclass
class FeatureResponse:
    """Unified response structure for the feature."""
    status: ResponseStatus
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        return {
            "status": self.status.value,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
    
    def is_successful(self) -> bool:
        """Check if the response indicates success."""
        return self.status == ResponseStatus.SUCCESS


class FeatureOrchestrator:
    """
    Main orchestrator class for the Granger Causality API Service.
    
    This class coordinates all layers and provides a unified interface
    for performing Granger causality analysis.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the feature orchestrator.
        
        Args:
            config: Feature configuration object. If None, uses defaults.
        """
        self.config = config or FeatureConfig()
        self._validate_config()
        self._layers = {}
        self._initialized = False
        
        # Initialize layers
        self._initialize_layers()
        
    def _validate_config(self) -> None:
        """Validate the configuration."""
        try:
            self.config.validate()
        except ValueError as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            raise
            
    def _initialize_layers(self) -> None:
        """Initialize all required layers."""
        try:
            # Note: Since no specific layers were defined in the input,
            # we create placeholder initialization logic
            logger.info("Initializing layers for Granger Causality API Service")
            
            # Placeholder for layer initialization
            # In a real implementation, this would import and initialize
            # specific layer classes based on the feature requirements
            
            self._initialized = True
            logger.info("All layers initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize layers: {str(e)}")
            self._initialized = False
            raise RuntimeError(f"Layer initialization failed: {str(e)}")
    
    def perform_granger_causality_test(
        self, 
        data: Dict[str, List[float]], 
        target_variable: str,
        predictor_variables: List[str]
    ) -> FeatureResponse:
        """
        Perform Granger causality test on the provided data.
        
        Args:
            data: Dictionary mapping variable names to time series data
            target_variable: Name of the variable to test as effect
            predictor_variables: Names of variables to test as causes
            
        Returns:
            FeatureResponse containing test results or error information
        """
        if not self._initialized:
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                errors=["Feature orchestrator not properly initialized"]
            )
        
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(
                data, target_variable, predictor_variables
            )
            if validation_errors:
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    errors=validation_errors
                )
            
            # Process the Granger causality test
            # Note: This is placeholder logic since no specific layers were defined
            results = self._process_granger_test(
                data, target_variable, predictor_variables
            )
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                data=results,
                metadata={
                    "config": {
                        "max_lag": self.config.max_lag,
                        "significance_level": self.config.significance_level,
                        "test_type": self.config.test_type,
                        "trend": self.config.trend
                    },
                    "target_variable": target_variable,
                    "predictor_variables": predictor_variables
                }
            )
            
        except Exception as e:
            logger.error(f"Error performing Granger causality test: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                errors=[str(e)],
                metadata={"traceback": traceback.format_exc()}
            )
    
    def _validate_inputs(
        self, 
        data: Dict[str, List[float]], 
        target_variable: str,
        predictor_variables: List[str]
    ) -> List[str]:
        """
        Validate input data for Granger causality test.
        
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        if not data:
            errors.append("No data provided")
            
        if target_variable not in data:
            errors.append(f"Target variable '{target_variable}' not found in data")
            
        for var in predictor_variables:
            if var not in data:
                errors.append(f"Predictor variable '{var}' not found in data")
        
        # Check data lengths
        if data and len(set(len(series) for series in data.values())) > 1:
            errors.append("All time series must have the same length")
            
        # Check minimum data length
        if data:
            min_length = min(len(series) for series in data.values())
            if min_length < self.config.max_lag + 2:
                errors.append(
                    f"Data length ({min_length}) must be greater than "
                    f"max_lag + 2 ({self.config.max_lag + 2})"
                )
        
        return errors
    
    def _process_granger_test(
        self,
        data: Dict[str, List[float]], 
        target_variable: str,
        predictor_variables: List[str]
    ) -> Dict[str, Any]:
        """
        Process the Granger causality test.
        
        This is a placeholder method that would orchestrate
        the actual layer interactions in a real implementation.
        """
        # Placeholder implementation
        results = {
            "tests": {},
            "summary": {
                "significant_predictors": [],
                "non_significant_predictors": []
            }
        }
        
        # Simulate test results for each predictor
        for predictor in predictor_variables:
            # Placeholder test result
            test_result = {
                "statistic": 2.5,  # Placeholder F-statistic
                "p_value": 0.08,   # Placeholder p-value
                "df": (self.config.max_lag, len(data[target_variable]) - 2 * self.config.max_lag - 1),
                "critical_value": 2.3,  # Placeholder critical value
                "reject_null": False
            }
            
            # Determine significance
            if test_result["p_value"] < self.config.significance_level:
                test_result["reject_null"] = True
                results["summary"]["significant_predictors"].append(predictor)
            else:
                results["summary"]["non_significant_predictors"].append(predictor)
                
            results["tests"][predictor] = test_result
        
        return results
    
    def get_status(self) -> FeatureResponse:
        """
        Get the current status of the feature orchestrator.
        
        Returns:
            FeatureResponse with status information
        """
        try:
            status_data = {
                "initialized": self._initialized,
                "config": {
                    "max_lag": self.config.max_lag,
                    "significance_level": self.config.significance_level,
                    "test_type": self.config.test_type,
                    "trend": self.config.trend,
                    "cache_enabled": self.config.cache_enabled
                },
                "layers": {
                    # Placeholder for actual layer status
                    "count": len(self._layers),
                    "status": "ready" if self._initialized else "not_initialized"
                }
            }
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS if self._initialized else ResponseStatus.WARNING,
                data=status_data,
                warnings=[] if self._initialized else ["Feature not fully initialized"]
            )
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                errors=[str(e)]
            )
    
    def shutdown(self) -> None:
        """
        Gracefully shutdown the feature orchestrator.
        
        This method ensures all layers are properly closed and resources released.
        """
        try:
            logger.info("Shutting down Granger Causality API Service orchestrator")
            
            # Cleanup layers
            for layer_name, layer in self._layers.items():
                try:
                    if hasattr(layer, 'close') and callable(getattr(layer, 'close')):
                        layer.close()
                    logger.info(f"Successfully shut down layer: {layer_name}")
                except Exception as e:
                    logger.error(f"Error shutting down layer {layer_name}: {str(e)}")
            
            self._layers.clear()
            self._initialized = False
            
            logger.info("Feature orchestrator shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            raise


# Example usage and testing
if __name__ == "__main__":
    # Create orchestrator with custom config
    config = FeatureConfig(
        max_lag=5,
        significance_level=0.05,
        test_type="ssr_ftest",
        verbose=True
    )
    
    orchestrator = FeatureOrchestrator(config)
    
    # Example data
    sample_data = {
        "variable_x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        "variable_y": [1.1, 2.2, 3.1, 4.3, 5.2, 6.1, 7.3, 8.2, 9.1, 10.2],
        "variable_z": [0.9, 1.8, 2.9, 3.8, 4.9, 5.8, 6.9, 7.8, 8.9, 9.8]
    }
    
    # Perform Granger causality test
    result = orchestrator.perform_granger_causality_test(
        data=sample_data,
        target_variable="variable_x",
        predictor_variables=["variable_y", "variable_z"]
    )
    
    # Print results
    print(f"Status: {result.status.value}")
    if result.is_successful():
        print(f"Results: {result.data}")
    else:
        print(f"Errors: {result.errors}")
    
    # Get status
    status = orchestrator.get_status()
    print(f"\nOrchestrator Status: {status.to_dict()}")
    
    # Shutdown
    orchestrator.shutdown()
