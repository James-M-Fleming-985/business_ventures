"""Error response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ValidationErrorDetail(BaseModel):
    """Validation error detail model."""

    field: str = Field(description="Field that failed validation")
    message: str = Field(description="Error message")
    type: str = Field(description="Error type")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "field": "email",
                    "message": "value is not a valid email address",
                    "type": "value_error.email",
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(description="Error message")
    status_code: int = Field(description="HTTP status code")
    path: str = Field(description="Request path")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional error details"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "Resource not found",
                    "status_code": 404,
                    "path": "/api/users/123",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "details": None,
                }
            ]
        }
    }
