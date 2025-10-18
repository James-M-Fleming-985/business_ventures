import time
import traceback
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.schemas.error import ErrorResponse, ErrorDetail


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="VALIDATION_ERROR",
                        message=str(e),
                        path=str(request.url.path),
                    )
                ).model_dump(),
            )
        except PermissionError as e:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="PERMISSION_DENIED",
                        message=str(e) or "Permission denied",
                        path=str(request.url.path),
                    )
                ).model_dump(),
            )
        except LookupError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="NOT_FOUND",
                        message=str(e) or "Resource not found",
                        path=str(request.url.path),
                    )
                ).model_dump(),
            )
        except TimeoutError as e:
            return JSONResponse(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="TIMEOUT_ERROR",
                        message=str(e) or "Request timeout",
                        path=str(request.url.path),
                    )
                ).model_dump(),
            )
        except Exception as e:
            # Log the full traceback for debugging
            traceback.print_exc()
            
            # Return generic error to client
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="INTERNAL_ERROR",
                        message="An unexpected error occurred",
                        path=str(request.url.path),
                    )
                ).model_dump(),
            )


def error_handler_middleware(app):
    """Configure error handler middleware."""
    app.add_middleware(ErrorHandlerMiddleware)