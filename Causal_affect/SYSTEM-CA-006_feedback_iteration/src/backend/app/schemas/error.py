"""Error response schemas."""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    """Validation error detail model."""

    loc: List[Union[str, int]] = Field(
        description="Location of the error",
        example=["body", "email"]
    )
    msg: str = Field(
        description="Error message",
        example="Invalid email format"
    )
    type: str = Field(
        description="Error type",
        example="value_error"
    )
    ctx: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Error context",
        example={"pattern": "^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"}
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "loc": ["body", "email"],
                "msg": "Invalid email format",
                "type": "value_error",
                "ctx": {"pattern": "^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"}
            }
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(
        description="Error type or code",
        example="validation_error"
    )
    message: str = Field(
        description="Human-readable error message",
        example="Request validation failed"
    )
    details: Optional[Union[List[ValidationError], Dict[str, Any], str]] = Field(
        default=None,
        description="Additional error details",
        example=[{
            "loc": ["body", "email"],
            "msg": "Invalid email format",
            "type": "value_error"
        }]
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request tracking ID",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="Error timestamp",
        example="2023-12-01T12:00:00Z"
    )
    path: Optional[str] = Field(
        default=None,
        description="Request path",
        example="/api/v1/users"
    )
    status_code: int = Field(
        description="HTTP status code",
        example=400
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "validation_error",
                "message": "Request validation failed",
                "details": [
                    {
                        "loc": ["body", "email"],
                        "msg": "Invalid email format",
                        "type": "value_error"
                    }
                ],
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2023-12-01T12:00:00Z",
                "path": "/api/v1/users",
                "status_code": 400
            }
        }
    }
