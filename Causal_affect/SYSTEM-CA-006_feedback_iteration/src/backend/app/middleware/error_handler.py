import time
import traceback
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global exception handling middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except StarletteHTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "message": exc.detail,
                        "status_code": exc.status_code,
                        "timestamp": time.time(),
                        "path": request.url.path,
                    }
                },
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "message": str(exc),
                        "status_code": 422,
                        "type": "validation_error",
                        "timestamp": time.time(),
                        "path": request.url.path,
                    }
                },
            )
        except Exception as exc:
            # Log the full traceback for debugging
            traceback_str = traceback.format_exc()
            print(f"Unhandled exception: {traceback_str}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "Internal server error",
                        "status_code": 500,
                        "type": "internal_error",
                        "timestamp": time.time(),
                        "path": request.url.path,
                    }
                },
            )


class BusinessException(Exception):
    """Base exception for business logic errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationException(BusinessException):
    """Exception for validation errors."""

    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class NotFoundException(BusinessException):
    """Exception for resource not found errors."""

    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", status_code=404)


class UnauthorizedException(BusinessException):
    """Exception for unauthorized access."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenException(BusinessException):
    """Exception for forbidden access."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class ConflictException(BusinessException):
    """Exception for conflict errors."""

    def __init__(self, message: str):
        super().__init__(message, status_code=409)
