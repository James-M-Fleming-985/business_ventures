"""Request and response logging middleware."""

import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and log details."""
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "")

        # Log request
        logger.info(
            f"Request started",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client": request.client.host if request.client else None,
                "request_id": request_id,
            },
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception(
                f"Request failed",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "request_id": request_id,
                    "error": str(exc),
                },
            )
            raise

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Request completed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "duration": f"{duration:.3f}s",
                "request_id": request_id,
            },
        )

        # Add custom headers
        response.headers["X-Process-Time"] = str(duration)
        if request_id:
            response.headers["X-Request-ID"] = request_id

        return response


def setup_logging_middleware(app: FastAPI) -> None:
    """Setup logging middleware."""
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Add middleware
    app.add_middleware(LoggingMiddleware)
