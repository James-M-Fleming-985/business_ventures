```python
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
from datetime import datetime
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
import os
from pathlib import Path


class DataFormatType(Enum):
    """Supported data format types"""
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    EXCEL = "excel"
    FEATHER = "feather"
    HDF = "hdf"
    PICKLE = "pickle"
    XML = "xml"


class ValidationStatus(Enum):
    """Validation status types"""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


@dataclass
class FormatSpecification:
    """Data format specification"""
    format_type: DataFormatType
    encoding: str = 'utf-8'
    compression: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None
    delimiter: Optional[str] = None
    header_rows: int = 1
    index_col: Optional[Union[int, str, List[Union[int, str]]]] = None
    date_format: Optional[str] = None
    decimal_separator: str = '.'
    thousands_separator: Optional[str] = None
    quote_char: str = '"'
    escape_char: Optional[str] = None
    null_values: List[str] = field(default_factory=lambda: ['', 'NA', 'NULL', 'null', 'None'])
    true_values: List[str] = field(default_factory=lambda: ['True', 'true', '1', 'yes', 'Yes'])
    false_values: List[str] = field(default_factory=lambda: ['False', 'false', '0', 'no', 'No'])
    custom_converters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Data validation result"""
    is_valid: bool
    status: ValidationStatus
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['status'] = self.status.value
        result['validation_timestamp'] = self.validation_timestamp.isoformat()
        return result


@dataclass
class ConversionResult:
    """Data conversion result"""
    success: bool
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    conversion_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['conversion_timestamp'] = self.conversion_timestamp.isoformat()
        return result


@dataclass
class TransformationRule:
    """Data transformation rule"""
    rule_name: str
    rule_type: str
    parameters: Dict[str, Any]
    apply_to_columns: Optional[List[str]] = None
    condition: Optional[str] = None
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataFormatOrchestrator:
    """
    Orchestrates data format operations including validation, conversion, and transformation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize DataFormatOrchestrator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        self._format_handlers = self._initialize_format_handlers()
        self._validators = self._initialize_validators()
        self._converters = self._initialize_converters()
        self._transformation_rules: List[TransformationRule] = []
        
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def _initialize_format_handlers(self) -> Dict[DataFormatType, Any]:
        """Initialize format handlers"""
        return {
            DataFormatType.CSV: self._handle_csv,
            DataFormatType.JSON: self._handle_json,
            DataFormatType.PARQUET: self._handle_parquet,
            DataFormatType.EXCEL: self._handle_excel,
            DataFormatType.FEATHER: self._handle_feather,
            DataFormatType.HDF: self._handle_hdf,
            DataFormatType.PICKLE: self._handle_pickle,
            DataFormatType.XML: self._handle_xml
        }
        
    def _initialize_validators(self) -> Dict[str, Any]:
        """Initialize validators"""
        return {
            'schema': self._validate_schema,
            'format': self._validate_format,
            'data_quality': self._validate_data_quality,
            'business_rules': self._validate_business_rules
        }
        
    def _initialize_converters(self) -> Dict[Tuple[DataFormatType, DataFormatType], Any]:
        """Initialize converters"""
        converters = {}
        for source in DataFormatType:
            for target in DataFormatType:
                converters[(source, target)] = self._create_converter(source, target)
        return converters
        
    def validate_data(
        self,
        data: Union[pd.DataFrame, str, Path],
        format_spec: FormatSpecification,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate data against format specification
        
        Args:
            data: Data to validate (DataFrame or file path)
            format_spec: Format specification
            validation_rules: Optional validation rules
            
        Returns:
            ValidationResult
        """
        self.logger.info(f"Validating data with format: {format_spec.format_type.value}")
        
        errors = []
        warnings = []
        metadata = {}
        
        try:
            # Load data if file path
            if isinstance(data, (str, Path)):
                df = self._load_data(data, format_spec)
            else:
                df = data
                
            # Validate format
            format_result = self._validate_format(df, format_spec)
            errors.extend(format_result.get('errors', []))
            warnings.extend(format_result.get('warnings', []))
            
            # Validate schema
            if format_spec.schema:
                schema_result = self._validate_schema(df, format_spec.schema)
                errors.extend(schema_result.get('errors', []))
                warnings.extend(schema_result.get('warnings', []))
                
            # Validate data quality
            quality_result = self._validate_data_quality(df, validation_rules or {})
            errors.extend(quality_result.get('errors', []))
            warnings.extend(quality_result.get('warnings', []))
            
            # Apply custom validation rules
            if validation_rules:
                custom_result = self._validate_business_rules(df, validation_rules)
                errors.extend(custom_result.get('errors', []))
                warnings.extend(custom_result.get('warnings', []))
                
            # Determine status
            if errors:
                status = ValidationStatus.INVALID
                is_valid = False
            elif warnings:
                status = ValidationStatus.WARNING
                is_valid = True
            else:
                status = ValidationStatus.VALID
                is_valid = True
                
            metadata.update({
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
            })
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            errors.append(f"Validation error: {str(e)}")
            status = ValidationStatus.INVALID
            is_valid = False
            
        return ValidationResult(
            is_valid=is_valid,
            status=status,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
        
    def convert_format(
        self,
        input_data: Union[pd.DataFrame, str, Path],
        source_format: FormatSpecification,
        target_format: FormatSpecification,
        output_path: Optional[str] = None,
        transformation_rules: Optional[List[TransformationRule]] = None
    ) -> ConversionResult:
        """
        Convert data from source format to target format
        
        Args:
            input_data: Input data
            source_format: Source format specification
            target_format: Target format specification
            output_path: Optional output file path
            transformation_rules: Optional transformation rules
            
        Returns:
            ConversionResult
        """
        self.logger.info(
            f"Converting from {source_format.format_type.value} "
            f"to {target_format.format_type.value}"
        )
        
        try:
            # Load data
            if isinstance(input_data, (str, Path)):
                df = self._load_data(input_data, source_format)
            else:
                df = input_data.copy()
                
            # Apply transformations
            if transformation_rules:
                df = self._apply_transformations(df, transformation_rules)
                
            # Convert format
            converter_key = (source_format.format_type, target_format.format_type)
            if converter_key in self._converters:
                df = self._converters[converter_key](df, source_format, target_format)
                
            # Save if output path provided
            if output_path:
                self._save_data(df, output_path, target_format)
                
            metadata = {
                'source_format': source_format.format_type.value,
                'target_format': target_format.format_type.value,
                'row_count': len(df),
                'column_count': len(df.columns),
                'transformations_applied': len(transformation_rules) if transformation_rules else 0
            }
            
            return ConversionResult(
                success=True,
                output_path=output_path,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Conversion error: {str(e)}")
            return ConversionResult(
                success=False,
                error_message=str(e)
            )
            
    def create_format_specification(
        self,
        format_type: Union[str, DataFormatType],
        **kwargs
    ) -> FormatSpecification:
        """
        Create a format specification
        
        Args:
            format_type: Format type
            **kwargs: Additional format parameters
            
        Returns:
            FormatSpecification
        """
        if isinstance(format_type, str):
            format_type = DataFormatType(format_type.lower())
            
        return FormatSpecification(
            format_type=format_type,
            **kwargs
        )
        
    def register_transformation_rule(
        self,
        rule: TransformationRule
    ) -> None:
        """
        Register a transformation rule
        
        Args:
            rule: Transformation rule
        """
        self._transformation_rules.append(rule)
        self._transformation_rules.sort(key=lambda x: x.priority, reverse=True)
        self.logger.info(f"Registered transformation rule: {rule.rule_name}")
        
    def apply_transformations(
        self,
        data: pd.DataFrame,
        rules: Optional[List[TransformationRule]] = None
    ) -> pd.DataFrame:
        """
        Apply transformation rules to data
        
        Args:
            data: Input DataFrame
            rules: Transformation rules (uses registered rules if None)
            
        Returns:
            Transformed DataFrame
        """
        rules = rules or self._transformation_rules
        return self._apply_transformations(data.copy(), rules)
        
    def _load_data(
        self,
        file_path: Union[str, Path],
        format_spec: FormatSpecification
    ) -> pd.DataFrame:
        """Load data from file"""
        handler = self._format_handlers.get(format_spec.format_type)
        if not handler:
            raise ValueError(f"Unsupported format: {format_spec.format_type}")
            
        return handler(file_path, format_spec, 'read')
        
    def _save_data(
        self,
        data: pd.DataFrame,
        file_path: Union[str, Path],
        format_spec: FormatSpecification
    ) -> None:
        """Save data to file"""
        handler = self._format_handlers.get(format_spec.format_type)
        if not handler:
            raise ValueError(f"Unsupported format: {format_spec.format_type}")
            
        # Create directory if needed
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        handler(file_path, format_spec, 'write', data)
        
    def _apply_transformations(
        self,
        data: pd.DataFrame,
        rules: List[TransformationRule]
    ) -> pd.DataFrame:
        """Apply transformation rules"""
        for rule in rules:
            if not rule.enabled:
                continue
                
            try:
                if rule.condition:
                    # Apply condition
                    mask = data.eval(rule.condition)
                    data = self._apply_single_transformation(data, rule, mask)
                else:
                    data = self._apply_single_transformation(data, rule)
                    
            except Exception as e:
                self.logger.warning(
                    f"Failed to apply transformation {rule.rule_name}: {str(e)}"
                )
                
        return data
        
    def _apply_single_transformation(
        self,
        data: pd.DataFrame,
        rule: TransformationRule,
        mask: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """Apply single transformation rule"""
        columns = rule.apply_to_columns or data.columns
        
        if rule.rule_type == 'rename':
            # Rename columns
            rename_map = rule.parameters.get('rename_map', {})
            data = data.rename(columns=rename_map)
            
        elif rule.rule_type == 'drop':
            # Drop columns
            data = data.drop(columns=[col for col in columns if col in data.columns])
            
        elif rule.rule_type == 'cast':
            # Cast data types
            dtype = rule.parameters.get('dtype', 'str')
            for col in columns:
                if col in data.columns:
                    if mask is not None:
                        data.loc[mask, col] = data.loc[mask, col].astype(dtype)
                    else:
                        data[col] = data[col].astype(dtype)
                        
        elif rule.rule_type == 'fillna':
            # Fill missing values
            value = rule.parameters.get('value', 0)
            method = rule.parameters.get('method')
            for col in columns:
                if col in data.columns:
                    if method:
                        if mask is not None:
                            data.loc[mask, col] = data.loc[mask, col].fillna(method=method)
                        else:
                            data[col] = data[col].fillna(method=method)
                    else:
                        if mask is not None:
                            data.loc[mask, col] = data.loc[mask, col].fillna(value)
                        else:
                            data[col] = data[col].fillna(value)
                            
        elif rule.rule_type == 'replace':
            # Replace values
            mapping = rule.parameters.get('mapping', {})
            for col in columns:
                if col in data.columns:
                    if mask is not None:
                        data.loc[mask, col] = data.loc[mask, col].replace(mapping)
                    else:
                        data[col] = data[col].replace(mapping)
                        
        elif rule.rule_type == 'normalize':
            # Normalize numeric columns
            method = rule.parameters.get('method', 'minmax')
            for col in columns:
                if col in data.columns and pd.api.types.is_numeric_dtype(data[col]):
                    if method == 'minmax':
                        if mask is not None:
                            col_data = data.loc[mask, col]
                            data.loc[mask, col] = (col_data - col_data.min()) / (col_data.max() - col_data.min())
                        else:
                            data[col] = (data[col] - data[col].min()) / (data[col].max() - data[col].min())
                    elif method == 'zscore':
                        if mask is not None:
                            col_data = data.loc[mask, col]
                            data.loc[mask, col] = (col_data - col_data.mean()) / col_data.std()
                        else:
                            data[col] = (data[col] - data[col].mean()) / data[col].std()
                            
        elif rule.rule_type == 'aggregate':
            # Aggregate data
            group_by = rule.parameters.get('group_by', [])
            agg_func = rule.parameters.get('agg_func', 'mean')
            if group_by:
                data = data.groupby(group_by).agg(agg_func).reset_index()
                
        elif rule.rule_type == 'custom':
            # Apply custom transformation
            func = rule.parameters.get('function')
            if func and callable(func):
                for col in columns:
                    if col in data.columns:
                        if mask is not None:
                            data.loc[mask, col] = data.loc[mask, col].apply(func)
                        else:
                            data[col] = data[col].apply(func)
                            
        return data
        
    def _validate_format(
        self,
        data: pd.DataFrame,
        format_spec: FormatSpecification
    ) -> Dict[str, List[str]]:
        """Validate data format"""
        errors = []
        warnings = []
        
        # Check encoding issues
        if format_spec.format_type in [DataFormatType.CSV, DataFormatType.JSON]:
            for col in data.columns:
                if data[col].dtype == object:
                    try:
                        data[col].str.encode(format_spec.encoding)
                    except Exception:
                        warnings.append(f"Column '{col}' may contain encoding issues")
                        
        return {'errors': errors, 'warnings': warnings}
        
    def _validate_schema(
        self,
        data: pd.DataFrame,
        schema: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Validate data schema"""
        errors = []
        warnings = []
        
        # Check required columns
        required_columns = schema.get('required_columns', [])
        for col in required_columns:
            if col not in data.columns:
                errors.append(f"Missing required column: {col}")
                
        # Check data types
        dtypes = schema.get('dtypes', {})
        for col, expected_dtype in dtypes.items():
            if col in data.columns:
                actual_dtype = str(data[col].dtype)
                if not self._dtype_compatible(actual_dtype, expected_dtype):
                    warnings.append(
                        f"Column '{col}' has dtype '{actual_dtype}', "
                        f"expected '{expected_dtype}'"
                    )
                    
        # Check constraints
        constraints = schema.get('constraints', {})
        for col, col_constraints in constraints.items():
            if col not in data.columns:
                continue
                
            # Check uniqueness
            if col_constraints.get('unique', False):
                if data[col].duplicated().any():
                    errors.append(f"Column '{col}' contains duplicate values")
                    
            # Check nullable
            if not col_constraints.get('nullable', True):
                if data[col].isna().any():
                    errors.append(f"Column '{col}' contains null values")
                    
            # Check min/max values
            if pd.api.types.is_numeric_dtype(data[col]):
                min_val = col_constraints.get('min')
                max_val = col_constraints.get('max')
                if min_val is not None and data[col].min() < min_val:
                    errors.append(f"Column '{col}' has values below minimum: {min_val}")
                if max_val is not None and data[col].max() > max_val:
                    errors.append(f"Column '{col}' has values above maximum: {max_val}")
                    
        return {'errors': errors, 'warnings': warnings}
        
    def _validate_data_quality(
        self,
        data: pd.DataFrame,
        rules: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Validate data quality"""
        errors = []
        warnings = []
        
        # Check completeness
        max_null_percentage = rules.get('max_null_percentage', 0.1)
        for col in data.columns:
            null_percentage = data[col].isna().sum() / len(data)
            if null_percentage > max_null_percentage:
                warnings.append(
                    f"Column '{col}' has {null_percentage:.1%} null values "
                    f"(threshold: {max_null_percentage:.1%})"
                )
                
        # Check duplicates
        if rules.get('check_duplicates', True):
            duplicate_count = data.duplicated().sum()
            if duplicate_count > 0:
                warnings.append(f"Data contains {duplicate_count} duplicate rows")
                
        # Check outliers for numeric columns
        if rules.get('check_outliers', True):
            for col in data.select_dtypes(include=[np.number]).columns:
                q1 = data[col].quantile(0.25)
                q3 = data[col].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = ((data[col] < lower_bound) | (data[col] > upper_bound)).sum()
                if outliers > 0:
                    warnings.append(f"Column '{col}' contains {outliers} outliers")
                    
        return {'errors': errors, 'warnings': warnings}
        
    def _validate_business_rules(
        self,
        data: pd.DataFrame,
        rules: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Validate business rules"""
        errors = []
        warnings = []
        
        # Apply custom validation rules
        for rule_name, rule_def in rules.items():
            if rule_name in ['max_null_percentage', 'check_duplicates', 'check_outliers']:
                continue  # Already handled in data quality validation
                
            try:
                if isinstance(rule_def, dict) and 'condition' in rule_def:
                    condition = rule_def['condition']
                    error_msg = rule_def.get('error_message', f"Business rule '{rule_name}' violated")
                    
                    # Evaluate condition
                    if not data.eval(condition).all():
                        errors.append(error_msg)
                        
            except Exception as e:
                warnings.append(f"Could not evaluate business rule '{rule_name}': {str(e)}")
                
        return {'errors': errors, 'warnings': warnings}
        
    def _dtype_compatible(self, actual: str, expected: str) -> bool:
        """Check if data types are compatible"""
        dtype_mappings = {
            'int': ['int64', 'int32', 'int16', 'int8', 'uint64', 'uint32', 'uint16', 'uint8'],
            'float': ['float64', 'float32', 'float16'],
            'str': ['object', 'string'],
            'bool': ['bool'],
            'datetime': ['datetime64[ns]', 'datetime64']
        }
        
        for dtype_group, dtypes in dtype_mappings.items():
            if expected in dtype_group and actual in dtypes:
                return True
            if expected in dtypes and actual in dtypes:
                return True
                
        return False
        
    def _create_converter(
        self,
        source: DataFormatType,
        target: DataFormatType
    ) -> Any:
        """Create converter function"""
        def converter(data, source_spec, target_spec):
            # Most conversions go through pandas DataFrame
            return data
        return converter
        
    # Format handlers
    def _handle_csv(self, file_path, format_spec, mode='read', data=None):
        """Handle CSV format"""
        if mode == 'read':
            return pd.read_csv(
                file_path,
                encoding=format_spec.encoding,
                delimiter=format_spec.delimiter or ',',
                header=0 if format_spec.header_rows > 0 else None,
                index_col=format_spec.index_col,
                na_values=format_spec.null_values,
                true_values=format_spec.true_values,
                false_values=format_spec.false_values,
                decimal=format_spec.decimal_separator,
                thousands=format_spec.thousands_separator,
                quotechar=format_spec.quote_char,
                escapechar=format_spec.escape_char,
                converters=format_spec.custom_converters
            )
        else:
            data.to_csv(
                file_path,
                encoding=format_spec.encoding,
                sep=format_spec.delimiter or ',',
                index=False,
                decimal=format_spec.decimal_separator,
                quotechar=format_spec.quote_char,
                escapechar=format_spec.escape_char
            )
            
    def _handle_json(self, file_path, format_spec, mode='read', data=None):
        """Handle JSON format"""
        if mode == 'read':
            return pd.read_json(
                file_path,
                encoding=format_spec.encoding,
                orient='records'
            )
        else:
            data.to_json(
                file_path,
                orient='records',
                date_format='iso',
                indent=2
            )
            
    def _handle_parquet(self, file_path, format_spec, mode='read', data=None):
        """Handle Parquet format"""
        if mode == 'read':
            return pd.read_parquet(file_path)
        else:
            data.to_parquet(
                file_path,
                compression=format_spec.compression or 'snappy'
            )
            
    def _handle_excel(self, file_path, format_spec, mode='read', data=None):
        """Handle Excel format"""
        if mode == 'read':
            return pd.read_excel(
                file_path,
                header=0 if format_spec.header_rows > 0 else None,
                index_col=format_spec.index_col,
                na_values=format_spec.null_values,
                converters=format_spec.custom_converters
            )
        else:
            data.to_excel(file_path, index=False)
            
    def _handle_feather(self, file_path, format_spec, mode='read', data=None):
        """Handle Feather format"""
        if mode == 'read':
            return pd.read_feather(file_path)
        else:
            data.to_feather(file_path)
            
    def _handle_hdf(self, file_path, format_spec, mode='read', data=None):
        """Handle HDF format"""
        if mode == 'read':
            return pd.read_hdf(file_path, 'data')
        else:
            data.to_hdf(file_path, key='data', mode='w')
            
    def _handle_pickle(self, file_path, format_spec, mode='read', data=None):
        """Handle Pickle format"""
        if mode == 'read':
            return pd.read_pickle(file_path)
        else:
            data.to_pickle(file_path)
            
    def _handle_xml(self, file_path, format_spec, mode='read', data=None):
        """Handle XML format"""
        if mode == 'read':
            try:
                return pd.read_xml(file_path)
            except AttributeError:
                # Fallback for older pandas versions
                import xml.etree.ElementTree as ET
                tree = ET.parse(file_path)
                root = tree.getroot()
                data = []
                for child in root:
                    row = {}
                    for elem in child:
                        row[elem.tag] = elem.text
                    data.append(row)
                return pd.DataFrame(data)
        else:
            try:
                data.to_xml(file_path)
            except AttributeError:
                # Fallback for older pandas versions
                data.to_csv(file_path.replace('.xml', '.csv'), index=False)
```