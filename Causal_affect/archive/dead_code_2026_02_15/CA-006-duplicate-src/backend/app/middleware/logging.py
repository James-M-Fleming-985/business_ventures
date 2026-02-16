import json
import time
import uuid
from typing import Callable, Dict, Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Store request ID in request state for use in logs
        request.state.request_id = request_id

        # Log request
        await self._log_request(request, request_id)

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        # Log response
        await self._log_response(request, response, process_time, request_id)

        return response

    async def _log_request(self, request: Request, request_id: str) -> None:
        """Log incoming request details."""
        log_data: Dict[str, Any] = {
            "request_id": request_id,
            "timestamp": time.time(),
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": self._get_safe_headers(request.headers),
            "client": f"{request.client.host}:{request.client.port}" if request.client else None,
        }

        # Log body for non-GET requests if it's not too large
        if request.method != "GET":
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) < 10000:  # 10KB limit
                try:
                    body = await request.body()
                    request._body = body  # Cache body for FastAPI to use
                    log_data["body"] = body.decode("utf-8") if body else None
                except Exception:
                    log_data["body"] = "<error reading body>"

        print(f"REQUEST: {json.dumps(log_data)}")

    async def _log_response(self, request: Request, response: Response, process_time: float, request_id: str) -> None:
        """Log response details."""
        log_data: Dict[str, Any] = {
            "request_id": request_id,
            "timestamp": time.time(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": process_time,
            "headers": self._get_safe_headers(response.headers),
        }

        print(f"RESPONSE: {json.dumps(log_data)}")

    def _get_safe_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Get headers with sensitive data masked."""
        safe_headers = dict(headers)
        sensitive_headers = [
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "x-csrf-token",
        ]

        for header in sensitive_headers:
            if header in safe_headers:
                safe_headers[header] = "***"

        return safe_headers


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure request ID is always present."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response
