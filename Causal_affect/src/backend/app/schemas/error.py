"""Error response schema models."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    path: str = Field(..., description="Request path that caused the error")
    timestamp: Optional[str] = Field(default=None, description="Error timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "NotFoundException",
                    "message": "Resource not found",
                    "path": "/api/v1/users/123",
                }
            ]
        }
    }


class ValidationErrorDetail(BaseModel):
    """Validation error detail model."""

    loc: list[str | int] = Field(..., description="Error location in request")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with detailed field errors."""

    details: list[dict[str, Any]] = Field(
        default_factory=list, description="Detailed validation errors"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "ValidationError",
                    "message": "Request validation failed",
                    "path": "/api/v1/users",
                    "details": [
                        {
                            "loc": ["body", "email"],
                            "msg": "Invalid email format",
                            "type": "value_error.email",
                        }
                    ],
                }
            ]
        }
    }
