"""
Feature Integration Module for Data Validation & Transformation Pipeline
Feature ID: FEATURE-CA-001-02

This module orchestrates the integration of multiple layers to provide
a complete data validation and transformation pipeline.
"""

from pathlib import Path
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import layer implementations
from layer_ca_001_02_01_schema_validator.src.implementation import (
    ValidationError,
    ValidationResult,
    SchemaValidator,
    DataStorage
)
from layer_ca_001_02_02_data_cleaner.src.implementation import DataCleaner
from layer_ca_001_02_03_transformer.src.implementation import (
    TransformerService,
    DataValidator,
    TransformationPipeline
)
from layer_ca_001_02_04_quality_checker.src.implementation import (
    QualityMetric,
    QualityScore,
    DataQualityChecker
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """Configuration for the Data Validation & Transformation Pipeline feature."""
    
    # Schema validation config
    schema_strict_mode: bool = True
    schema_validation_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Data cleaning config
    remove_duplicates: bool = True
    handle_missing_values: str = "drop"  # Options: "drop", "fill", "interpolate"
    outlier_detection_method: Optional[str] = "iqr"  # Options: "iqr", "zscore", None
    
    # Transformation config
    transformation_rules: List[Dict[str, Any]] = field(default_factory=list)
    enable_parallel_processing: bool = False
    
    # Quality checking config
    quality_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "completeness": 0.95,
        "accuracy": 0.98,
        "consistency": 0.99
    })
    
    # General config
    enable_caching: bool = True
    max_processing_time: int = 300  # seconds
    error_tolerance: float = 0.05  # 5% error tolerance


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations."""
    
    success: bool
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Operation results
    validation_result: Optional[ValidationResult] = None
    cleaned_data: Optional[Any] = None
    transformed_data: Optional[Any] = None
    quality_scores: Optional[Dict[str, QualityScore]] = None
    
    # Metadata
    processing_time: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeatureOrchestrator:
    """
    Orchestrates the Data Validation & Transformation Pipeline.
    
    This class coordinates the interaction between Schema Validator,
    Data Cleaner, Transformer, and Quality Checker layers to provide
    a complete data processing pipeline.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the Feature Orchestrator.
        
        Args:
            config: Feature configuration. If None, uses default configuration.
        """
        self.config = config or FeatureConfig()
        
        # Initialize layer instances
        self._initialize_layers()
        
        # Initialize data storage if caching is enabled
        if self.config.enable_caching:
            self.data_storage = DataStorage()
        else:
            self.data_storage = None
            
        logger.info("Feature Orchestrator initialized successfully")
    
    def _initialize_layers(self) -> None:
        """Initialize all layer instances with error handling."""
        try:
            # Initialize Schema Validator
            self.schema_validator = SchemaValidator()
            logger.info("Schema Validator initialized")
            
            # Initialize Data Cleaner
            self.data_cleaner = DataCleaner()
            logger.info("Data Cleaner initialized")
            
            # Initialize Transformer components
            self.transformer_service = TransformerService()
            self.data_validator = DataValidator()
            self.transformation_pipeline = TransformationPipeline()
            logger.info("Transformer components initialized")
            
            # Initialize Quality Checker
            self.quality_checker = DataQualityChecker()
            logger.info("Quality Checker initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize layers: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def process_data(self, 
                    data: Any, 
                    schema: Optional[Dict[str, Any]] = None,
                    transformations: Optional[List[Dict[str, Any]]] = None) -> FeatureResponse:
        """
        Process data through the complete validation and transformation pipeline.
        
        Args:
            data: Input data to process
            schema: Optional schema for validation
            transformations: Optional list of transformations to apply
            
        Returns:
            FeatureResponse containing results from all processing stages
        """
        start_time = datetime.now()
        response = FeatureResponse(success=False, message="Processing started")
        
        try:
            # Step 1: Schema Validation
            if schema:
                validation_result = self._validate_schema(data, schema)
                response.validation_result = validation_result
                
                if not validation_result.is_valid and self.config.schema_strict_mode:
                    response.message = "Schema validation failed"
                    response.errors.extend(validation_result.errors)
                    return response
            
            # Step 2: Data Cleaning
            cleaned_data = self._clean_data(data)
            response.cleaned_data = cleaned_data
            
            # Step 3: Data Transformation
            if transformations or self.config.transformation_rules:
                transformed_data = self._transform_data(
                    cleaned_data, 
                    transformations or self.config.transformation_rules
                )
                response.transformed_data = transformed_data
            else:
                response.transformed_data = cleaned_data
            
            # Step 4: Quality Check
            quality_scores = self._check_quality(response.transformed_data)
            response.quality_scores = quality_scores
            
            # Evaluate overall success
            response.success = self._evaluate_pipeline_success(response)
            response.message = "Data processing completed successfully" if response.success else "Data processing completed with issues"
            
        except Exception as e:
            error_msg = f"Pipeline processing error: {str(e)}"
            logger.error(error_msg)
            response.errors.append(error_msg)
            response.message = "Pipeline processing failed"
            
        finally:
            # Calculate processing time
            response.processing_time = (datetime.now() - start_time).total_seconds()
            
            # Store results if caching is enabled
            if self.config.enable_caching and self.data_storage and response.success:
                self._cache_results(response)
        
        return response
    
    def _validate_schema(self, data: Any, schema: Dict[str, Any]) -> ValidationResult:
        """
        Validate data against schema.
        
        Args:
            data: Data to validate
            schema: Schema definition
            
        Returns:
            ValidationResult from schema validator
        """
        try:
            return self.schema_validator.validate(data, schema)
        except Exception as e:
            logger.error(f"Schema validation error: {str(e)}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[]
            )
    
    def _clean_data(self, data: Any) -> Any:
        """
        Clean data using the Data Cleaner layer.
        
        Args:
            data: Data to clean
            
        Returns:
            Cleaned data
        """
        try:
            # Apply cleaning operations based on config
            cleaned_data = data
            
            if hasattr(self.data_cleaner, 'remove_duplicates') and self.config.remove_duplicates:
                cleaned_data = self.data_cleaner.remove_duplicates(cleaned_data)
            
            if hasattr(self.data_cleaner, 'handle_missing'):
                cleaned_data = self.data_cleaner.handle_missing(
                    cleaned_data, 
                    method=self.config.handle_missing_values
                )
            
            if hasattr(self.data_cleaner, 'detect_outliers') and self.config.outlier_detection_method:
                cleaned_data = self.data_cleaner.detect_outliers(
                    cleaned_data,
                    method=self.config.outlier_detection_method
                )
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Data cleaning error: {str(e)}")
            raise
    
    def _transform_data(self, data: Any, transformations: List[Dict[str, Any]]) -> Any:
        """
        Transform data using the Transformer layer.
        
        Args:
            data: Data to transform
            transformations: List of transformation rules
            
        Returns:
            Transformed data
        """
        try:
            # Validate data before transformation
            if hasattr(self.data_validator, 'validate'):
                validation_result = self.data_validator.validate(data)
                if not validation_result:
                    raise ValueError("Data validation failed before transformation")
            
            # Apply transformations
            transformed_data = data
            for transformation in transformations:
                if hasattr(self.transformation_pipeline, 'apply_transformation'):
                    transformed_data = self.transformation_pipeline.apply_transformation(
                        transformed_data,
                        transformation
                    )
                elif hasattr(self.transformer_service, 'transform'):
                    transformed_data = self.transformer_service.transform(
                        transformed_data,
                        transformation
                    )
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"Data transformation error: {str(e)}")
            raise
    
    def _check_quality(self, data: Any) -> Dict[str, QualityScore]:
        """
        Check data quality using the Quality Checker layer.
        
        Args:
            data: Data to check
            
        Returns:
            Dictionary of quality scores by metric
        """
        try:
            quality_scores = {}
            
            # Check each quality metric
            for metric_name, threshold in self.config.quality_thresholds.items():
                if hasattr(self.quality_checker, f'check_{metric_name}'):
                    metric_method = getattr(self.quality_checker, f'check_{metric_name}')
                    score = metric_method(data)
                    quality_scores[metric_name] = QualityScore(
                        metric=QualityMetric(name=metric_name, threshold=threshold),
                        score=score,
                        passed=score >= threshold
                    )
                elif hasattr(self.quality_checker, 'calculate_quality'):
                    score = self.quality_checker.calculate_quality(data, metric_name)
                    quality_scores[metric_name] = QualityScore(
                        metric=QualityMetric(name=metric_name, threshold=threshold),
                        score=score,
                        passed=score >= threshold
                    )
            
            return quality_scores
            
        except Exception as e:
            logger.error(f"Quality checking error: {str(e)}")
            return {}
    
    def _evaluate_pipeline_success(self, response: FeatureResponse) -> bool:
        """
        Evaluate overall pipeline success based on response data.
        
        Args:
            response: Feature response to evaluate
            
        Returns:
            True if pipeline executed successfully, False otherwise
        """
        # Check for critical errors
        if response.errors:
            error_rate = len(response.errors) / max(1, len(response.errors) + len(response.warnings))
            if error_rate > self.config.error_tolerance:
                return False
        
        # Check validation result
        if response.validation_result and not response.validation_result.is_valid:
            return False
        
        # Check quality scores
        if response.quality_scores:
            failed_metrics = [
                metric for metric, score in response.quality_scores.items() 
                if not score.passed
            ]
            if failed_metrics:
                logger.warning(f"Quality metrics failed: {failed_metrics}")
                return False
        
        # Check processing time
        if response.processing_time and response.processing_time > self.config.max_processing_time:
            logger.warning(f"Processing time exceeded limit: {response.processing_time}s")
            response.warnings.append(f"Processing time exceeded limit: {response.processing_time}s")
        
        return True
    
    def _cache_results(self, response: FeatureResponse) -> None:
        """
        Cache processing results for future use.
        
        Args:
            response: Response to cache
        """
        try:
            if self.data_storage and hasattr(self.data_storage, 'store'):
                cache_key = f"pipeline_result_{response.timestamp.isoformat()}"
                self.data_storage.store(cache_key, response)
                logger.info(f"Results cached with key: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache results: {str(e)}")
    
    def validate_only(self, data: Any, schema: Dict[str, Any]) -> FeatureResponse:
        """
        Perform only schema validation without full pipeline processing.
        
        Args:
            data: Data to validate
            schema: Schema definition
            
        Returns:
            FeatureResponse with validation results
        """
        response = FeatureResponse(success=False, message="Validation started")
        
        try:
            validation_result = self._validate_schema(data, schema)
            response.validation_result = validation_result
            response.success = validation_result.is_valid
            response.message = "Validation completed successfully" if response.success else "Validation failed"
            
            if not response.success:
                response.errors.extend(validation_result.errors)
            
            if validation_result.warnings:
                response.warnings.extend(validation_result.warnings)
                
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(error_msg)
            response.errors.append(error_msg)
            response.message = "Validation failed with error"
        
        return response
    
    def transform_only(self, data: Any, transformations: List[Dict[str, Any]]) -> FeatureResponse:
        """
        Perform only data transformation without validation or quality checks.
        
        Args:
            data: Data to transform
            transformations: List of transformation rules
            
        Returns:
            FeatureResponse with transformation results
        """
        response = FeatureResponse(success=False, message="Transformation started")
        
        try:
            transformed_data = self._transform_data(data, transformations)
            response.transformed_data = transformed_data
            response.success = True
            response.message = "Transformation completed successfully"
            
        except Exception as e:
            error_msg = f"Transformation error: {str(e)}"
            logger.error(error_msg)
            response.errors.append(error_msg)
            response.message = "Transformation failed"
        
        return response
    
    def check_quality_only(self, data: Any) -> FeatureResponse:
        """
        Perform only quality checks without other processing.
        
        Args:
            data: Data to check
            
        Returns:
            FeatureResponse with quality check results
        """
        response = FeatureResponse(success=False, message="Quality check started")
        
        try:
            quality_scores = self._check_quality(data)
            response.quality_scores = quality_scores
            
            # Determine success based on quality scores
            all_passed = all(score.passed for score in quality_scores.values())
            response.success = all_passed
            response.message = "Quality check passed" if all_passed else "Quality check failed"
            
            # Add warnings for failed metrics
            for metric_name, score in quality_scores.items():
                if not score.passed:
                    response.warnings.append(
                        f"Quality metric '{metric_name}' failed: {score.score:.2f} < {score.metric.threshold}"
                    )
            
        except Exception as e:
            error_msg = f"Quality check error: {str(e)}"
            logger.error(error_msg)
            response.errors.append(error_msg)
            response.message = "Quality check failed with error"
        
        return response