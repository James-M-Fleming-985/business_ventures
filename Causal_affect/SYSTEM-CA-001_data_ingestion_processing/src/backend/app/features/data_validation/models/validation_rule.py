from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict


class ValidationRuleType(str, Enum):
    FIELD_REQUIRED = "field_required"
    FIELD_TYPE = "field_type"
    FIELD_RANGE = "field_range"
    FIELD_PATTERN = "field_pattern"
    FIELD_LENGTH = "field_length"
    FIELD_UNIQUE = "field_unique"
    FIELD_REFERENCE = "field_reference"
    RECORD_CONSTRAINT = "record_constraint"
    CROSS_FIELD = "cross_field"
    CUSTOM_SCRIPT = "custom_script"


class ValidationRuleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    DEPRECATED = "deprecated"


class RuleSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_EQUALS = "greater_than_equals"
    LESS_THAN = "less_than"
    LESS_THAN_EQUALS = "less_than_equals"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    MATCHES_PATTERN = "matches_pattern"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"
    NOT_BETWEEN = "not_between"


class RuleActionType(str, Enum):
    REJECT = "reject"
    FLAG = "flag"
    TRANSFORM = "transform"
    SET_DEFAULT = "set_default"
    NOTIFY = "notify"
    LOG = "log"


class ValidationRuleCondition(BaseModel):
    """Represents a condition for validation rule evaluation"""
    
    field_path: str = Field(..., description="JSONPath or field reference")
    operator: RuleConditionOperator
    value: Optional[Union[str, int, float, bool, List[Any], Dict[str, Any]]] = None
    case_sensitive: bool = False
    data_type: Optional[str] = None
    
    @field_validator("value")
    @classmethod
    def validate_value(cls, v, info):
        operator = info.data.get("operator")
        if operator in [RuleConditionOperator.IS_NULL, RuleConditionOperator.IS_NOT_NULL] and v is not None:
            raise ValueError(f"Operator {operator} should not have a value")
        elif operator not in [RuleConditionOperator.IS_NULL, RuleConditionOperator.IS_NOT_NULL] and v is None:
            raise ValueError(f"Operator {operator} requires a value")
        return v


class ValidationRuleAction(BaseModel):
    """Action to take when validation rule is triggered"""
    
    action_type: RuleActionType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class ValidationRuleMetadata(BaseModel):
    """Additional metadata for validation rules"""
    
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    business_impact: Optional[str] = None
    compliance_requirement: Optional[str] = None
    documentation_url: Optional[str] = None
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class ValidationRuleConfig(BaseModel):
    """Configuration for rule execution"""
    
    conditions: List[ValidationRuleCondition] = Field(..., min_length=1)
    condition_logic: str = Field("AND", pattern="^(AND|OR)$")
    actions: List[ValidationRuleAction] = Field(..., min_length=1)
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    bypass_conditions: Optional[List[ValidationRuleCondition]] = None
    execution_order: int = Field(default=0, ge=0)
    

class ValidationRuleBase(BaseModel):
    """Base validation rule schema"""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    rule_type: ValidationRuleType
    severity: RuleSeverity = Field(default=RuleSeverity.ERROR)
    status: ValidationRuleStatus = Field(default=ValidationRuleStatus.DRAFT)
    config: ValidationRuleConfig
    metadata: Optional[ValidationRuleMetadata] = None
    is_system: bool = Field(default=False, description="System rules cannot be deleted")
    

class ValidationRuleCreate(ValidationRuleBase):
    """Schema for creating validation rules"""
    
    data_source_id: UUID
    applies_to_fields: List[str] = Field(..., min_length=1)
    applies_to_tables: Optional[List[str]] = None
    

class ValidationRuleUpdate(BaseModel):
    """Schema for updating validation rules"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    rule_type: Optional[ValidationRuleType] = None
    severity: Optional[RuleSeverity] = None
    status: Optional[ValidationRuleStatus] = None
    config: Optional[ValidationRuleConfig] = None
    metadata: Optional[ValidationRuleMetadata] = None
    applies_to_fields: Optional[List[str]] = Field(None, min_length=1)
    applies_to_tables: Optional[List[str]] = None
    
    model_config = ConfigDict(extra="forbid")


class ValidationRule(ValidationRuleBase):
    """Validation rule response schema"""
    
    id: UUID = Field(default_factory=uuid4)
    data_source_id: UUID
    applies_to_fields: List[str]
    applies_to_tables: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    version: int = Field(default=1, ge=1)
    execution_stats: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class ValidationRuleInDB(ValidationRule):
    """Validation rule database representation"""
    
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    organization_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426655440000",
                "name": "Email Format Validation",
                "description": "Validates email addresses in user data",
                "rule_type": "field_pattern",
                "severity": "error",
                "status": "active",
                "data_source_id": "456e7890-e89b-12d3-a456-426655440000",
                "applies_to_fields": ["email", "contact_email"],
                "config": {
                    "conditions": [
                        {
                            "field_path": "$.email",
                            "operator": "matches_pattern",
                            "value": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                            "case_sensitive": False
                        }
                    ],
                    "condition_logic": "AND",
                    "actions": [
                        {
                            "action_type": "reject",
                            "parameters": {
                                "error_code": "INVALID_EMAIL"
                            }
                        }
                    ],
                    "error_message": "Invalid email format"
                },
                "metadata": {
                    "tags": ["email", "validation"],
                    "category": "data_quality",
                    "compliance_requirement": "GDPR"
                }
            }
        }
    )
