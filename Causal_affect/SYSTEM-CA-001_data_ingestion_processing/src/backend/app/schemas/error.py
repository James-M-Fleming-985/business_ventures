from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    """Field validation error."""
    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Validation error message")
    code: str = Field(..., description="Error code")
    

class ErrorDetail(BaseModel):
    """Error detail information."""
    code: str = Field(..., description="Error code for client handling")
    message: str = Field(..., description="Human-readable error message")
    path: Optional[str] = Field(None, description="API path where error occurred")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    validation_errors: Optional[List[ValidationError]] = Field(
        None, 
        description="Field-specific validation errors"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error context"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: ErrorDetail
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid request data",
                        "path": "/api/v1/users",
                        "timestamp": "2023-11-20T10:30:00Z",
                        "validation_errors": [
                            {
                                "field": "email",
                                "message": "Invalid email format",
                                "code": "invalid_format"
                            }
                        ]
                    }
                },
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "User not found",
                        "path": "/api/v1/users/123",
                        "timestamp": "2023-11-20T10:30:00Z"
                    }
                },
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                        "timestamp": "2023-11-20T10:30:00Z",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                }
            ]
        }