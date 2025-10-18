"""Data validation services."""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import re
from abc import ABC, abstractmethod


class ValidationSeverity(str, Enum):
    """Validation error severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.field = field
        self.severity = severity
        self.details = details or {}


class ValidationIssue(BaseModel):
    """Represents a single validation issue."""
    field: Optional[str] = None
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    code: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    """Result of a validation operation."""
    is_valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def error_count(self) -> int:
        return len([i for i in self.issues if i.severity == ValidationSeverity.ERROR])
    
    @property
    def warning_count(self) -> int:
        return len([i for i in self.issues if i.severity == ValidationSeverity.WARNING])
    
    def add_issue(
        self,
        message: str,
        field: Optional[str] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a validation issue to the result."""
        issue = ValidationIssue(
            field=field,
            message=message,
            severity=severity,
            code=code,
            details=details or {},
        )
        self.issues.append(issue)
        if severity == ValidationSeverity.ERROR:
            self.is_valid = False


@runtime_checkable
class ValidationRule(Protocol):
    """Protocol for validation rules."""
    
    async def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate a value and return the result."""
        ...


class BaseValidationRule(ABC):
    """Base class for validation rules."""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    async def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate a value and return the result."""
        pass


class RequiredFieldRule(BaseValidationRule):
    """Validates that a field is present and not empty."""
    
    def __init__(self, field_name: str, allow_empty: bool = False):
        super().__init__(f"RequiredField:{field_name}")
        self.field_name = field_name
        self.allow_empty = allow_empty
    
    async def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        if value is None:
            result.add_issue(
                message=f"Field '{self.field_name}' is required",
                field=self.field_name,
                code="required_field_missing",
            )
        elif not self.allow_empty and isinstance(value, (str, list, dict)) and not value:
            result.add_issue(
                message=f"Field '{self.field_name}' cannot be empty",
                field=self.field_name,
                code="required_field_empty",
            )
        
        return result


class RegexRule(BaseValidationRule):
    """Validates string values against a regex pattern."""
    
    def __init__(self, pattern: str, field_name: Optional[str] = None, error_message: Optional[str] = None):
        super().__init__(f"Regex:{pattern}")
        self.pattern = re.compile(pattern)
        self.field_name = field_name
        self.error_message = error_message or f"Value does not match pattern: {pattern}"
    
    async def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        if value is None:
            return result
        
        if not isinstance(value, str):
            result.add_issue(
                message="Value must be a string for regex validation",
                field=self.field_name,
                code="invalid_type_for_regex",
                details={"expected_type": "str", "actual_type": type(value).__name__},
            )
            return result
        
        if not self.pattern.match(value):
            result.add_issue(
                message=self.error_message,
                field=self.field_name,
                code="regex_mismatch",
                details={"pattern": self.pattern.pattern, "value": value},
            )
        
        return result


class RangeRule(BaseValidationRule):
    """Validates numeric values are within a specified range."""
    
    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        field_name: Optional[str] = None,
    ):
        super().__init__(f"Range:{min_value}-{max_value}")
        self.min_value = min_value
        self.max_value = max_value
        self.field_name = field_name
    
    async def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        if value is None:
            return result
        
        if not isinstance(value, (int, float)):
            result.add_issue(
                message="Value must be numeric for range validation",
                field=self.field_name,
                code="invalid_type_for_range",
                details={"expected_type": "numeric", "actual_type": type(value).__name__},
            )
            return result
        
        if self.min_value is not None and value < self.min_value:
            result.add_issue(
                message=f"Value must be at least {self.min_value}",
                field=self.field_name,
                code="below_minimum",
                details={"min_value": self.min_value, "actual_value": value},
            )
        
        if self.max_value is not None and value > self.max_value:
            result.add_issue(
                message=f"Value must be at most {self.max_value}",
                field=self.field_name,
                code="above_maximum",
                details={"max_value": self.max_value, "actual_value": value},
            )
        
        return result


class CompositeRule(BaseValidationRule):
    """Combines multiple validation rules."""
    
    def __init__(self, rules: List[ValidationRule], name: Optional[str] = None):
        super().__init__(name or "CompositeRule")
        self.rules = rules
    
    async def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        for rule in self.rules:
            sub_result = await rule.validate(value, context)
            result.issues.extend(sub_result.issues)
            if not sub_result.is_valid:
                result.is_valid = False
        
        return result


class DataValidationService:
    """Service for validating data using configurable rules."""
    
    def __init__(self):
        self._rule_registry: Dict[str, ValidationRule] = {}
    
    def register_rule(self, name: str, rule: ValidationRule) -> None:
        """Register a validation rule."""
        self._rule_registry[name] = rule
    
    def get_rule(self, name: str) -> Optional[ValidationRule]:
        """Get a registered validation rule by name."""
        return self._rule_registry.get(name)
    
    async def validate_with_rule(
        self,
        rule_name: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Validate a value using a registered rule."""
        rule = self.get_rule(rule_name)
        if not rule:
            raise ValidationError(f"Rule '{rule_name}' not found")
        
        return await rule.validate(value, context)
    
    async def validate_dict(
        self,
        data: Dict[str, Any],
        field_rules: Dict[str, List[ValidationRule]],
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Validate a dictionary using field-specific rules."""
        result = ValidationResult(is_valid=True)
        
        for field_name, rules in field_rules.items():
            field_value = data.get(field_name)
            
            for rule in rules:
                field_result = await rule.validate(field_value, context)
                
                # Add field name to issues if not already set
                for issue in field_result.issues:
                    if issue.field is None:
                        issue.field = field_name
                
                result.issues.extend(field_result.issues)
                if not field_result.is_valid:
                    result.is_valid = False
        
        result.metadata["validated_fields"] = list(field_rules.keys())
        return result
    
    async def validate_list(
        self,
        data: List[Any],
        item_rules: List[ValidationRule],
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Validate a list using item-specific rules."""
        result = ValidationResult(is_valid=True)
        
        for index, item in enumerate(data):
            for rule in item_rules:
                item_result = await rule.validate(item, context)
                
                # Add index to issues
                for issue in item_result.issues:
                    if issue.field:
                        issue.field = f"[{index}].{issue.field}"
                    else:
                        issue.field = f"[{index}]"
                
                result.issues.extend(item_result.issues)
                if not item_result.is_valid:
                    result.is_valid = False
        
        result.metadata["validated_items"] = len(data)
        return result


__all__ = [
    "ValidationSeverity",
    "ValidationError",
    "ValidationIssue",
    "ValidationResult",
    "ValidationRule",
    "BaseValidationRule",
    "RequiredFieldRule",
    "RegexRule",
    "RangeRule",
    "CompositeRule",
    "DataValidationService",
]
