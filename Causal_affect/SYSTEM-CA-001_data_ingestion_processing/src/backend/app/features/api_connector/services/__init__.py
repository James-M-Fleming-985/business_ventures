"""Services for API Connector feature."""

from typing import Any, Dict, Optional, Union
import httpx
from pydantic import BaseModel, HttpUrl, Field
import logging
from enum import Enum
import asyncio
from functools import wraps
import time

logger = logging.getLogger(__name__)


class HTTPMethod(str, Enum):
    """Supported HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class RetryConfig(BaseModel):
    """Configuration for retry behavior."""
    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff_factor: float = Field(default=2.0, ge=1.0, le=5.0)
    max_delay: float = Field(default=60.0, ge=1.0, le=300.0)
    retry_on_status: list[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])


class RequestConfig(BaseModel):
    """Configuration for HTTP requests."""
    timeout: float = Field(default=30.0, ge=1.0, le=300.0)
    follow_redirects: bool = Field(default=True)
    verify_ssl: bool = Field(default=True)
    retry_config: RetryConfig = Field(default_factory=RetryConfig)


class APIResponse(BaseModel):
    """Standardized API response model."""
    status_code: int
    headers: Dict[str, str]
    data: Optional[Union[Dict[str, Any], list, str]] = None
    error: Optional[str] = None
    elapsed_ms: float
    

class APIConnectorException(Exception):
    """Base exception for API Connector."""
    pass


class RequestException(APIConnectorException):
    """Exception for request failures."""
    pass


class ResponseException(APIConnectorException):
    """Exception for response processing failures."""
    pass


def retry_with_backoff(retry_config: RetryConfig):
    """Decorator for implementing retry logic with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            delay = 1.0
            
            for attempt in range(retry_config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (httpx.HTTPStatusError, httpx.RequestError) as e:
                    last_exception = e
                    
                    if isinstance(e, httpx.HTTPStatusError):
                        if e.response.status_code not in retry_config.retry_on_status:
                            raise
                    
                    if attempt < retry_config.max_attempts - 1:
                        sleep_time = min(delay, retry_config.max_delay)
                        logger.warning(
                            f"Request failed (attempt {attempt + 1}/{retry_config.max_attempts}), "
                            f"retrying in {sleep_time:.1f}s: {str(e)}"
                        )
                        await asyncio.sleep(sleep_time)
                        delay *= retry_config.backoff_factor
                    else:
                        raise RequestException(f"Max retries exceeded: {str(last_exception)}") from last_exception
                        
            raise RequestException(f"Unexpected retry loop exit")
        return wrapper
    return decorator


class RequestBuilder:
    """Builds HTTP requests with validation."""
    
    @staticmethod
    def build(
        method: HTTPMethod,
        url: HttpUrl,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        auth: Optional[tuple[str, str]] = None,
    ) -> Dict[str, Any]:
        """Build request parameters."""
        request_params = {
            "method": method.value,
            "url": str(url),
        }
        
        if headers:
            request_params["headers"] = headers
        if params:
            request_params["params"] = params
        if json_data:
            request_params["json"] = json_data
        if data:
            request_params["data"] = data
        if auth:
            request_params["auth"] = auth
            
        return request_params


class ResponseHandler:
    """Handles and processes HTTP responses."""
    
    @staticmethod
    def process(response: httpx.Response, elapsed_ms: float) -> APIResponse:
        """Process HTTP response into standardized format."""
        try:
            data = None
            error = None
            
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    data = response.json()
                except Exception as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    data = response.text
            else:
                data = response.text if response.text else None
                
            if response.is_error:
                error = f"HTTP {response.status_code}: {response.reason_phrase}"
                
            return APIResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                data=data,
                error=error,
                elapsed_ms=elapsed_ms,
            )
        except Exception as e:
            raise ResponseException(f"Failed to process response: {str(e)}") from e


class HTTPClient:
    """Async HTTP client with retry and error handling."""
    
    def __init__(self, config: Optional[RequestConfig] = None):
        self.config = config or RequestConfig()
        self._client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        
    async def connect(self):
        """Initialize HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                follow_redirects=self.config.follow_redirects,
                verify=self.config.verify_ssl,
            )
            
    async def disconnect(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            
    @retry_with_backoff(RetryConfig())
    async def request(
        self,
        method: HTTPMethod,
        url: HttpUrl,
        **kwargs,
    ) -> APIResponse:
        """Execute HTTP request with retry logic."""
        if not self._client:
            raise RequestException("HTTP client not connected")
            
        request_params = RequestBuilder.build(
            method=method,
            url=url,
            **kwargs,
        )
        
        start_time = time.time()
        
        try:
            response = await self._client.request(**request_params)
            elapsed_ms = (time.time() - start_time) * 1000
            
            response.raise_for_status()
            
            return ResponseHandler.process(response, elapsed_ms)
            
        except httpx.RequestError as e:
            raise RequestException(f"Request failed: {str(e)}") from e
        except httpx.HTTPStatusError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return ResponseHandler.process(e.response, elapsed_ms)


class APIConnectorService:
    """Main service for API connections."""
    
    def __init__(self, config: Optional[RequestConfig] = None):
        self.config = config or RequestConfig()
        self.client = HTTPClient(self.config)
        
    async def __aenter__(self):
        await self.client.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()
        
    async def get(
        self,
        url: HttpUrl,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute GET request."""
        return await self.client.request(
            method=HTTPMethod.GET,
            url=url,
            headers=headers,
            params=params,
            **kwargs,
        )
        
    async def post(
        self,
        url: HttpUrl,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute POST request."""
        return await self.client.request(
            method=HTTPMethod.POST,
            url=url,
            headers=headers,
            json_data=json_data,
            data=data,
            **kwargs,
        )
        
    async def put(
        self,
        url: HttpUrl,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute PUT request."""
        return await self.client.request(
            method=HTTPMethod.PUT,
            url=url,
            headers=headers,
            json_data=json_data,
            data=data,
            **kwargs,
        )
        
    async def patch(
        self,
        url: HttpUrl,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute PATCH request."""
        return await self.client.request(
            method=HTTPMethod.PATCH,
            url=url,
            headers=headers,
            json_data=json_data,
            data=data,
            **kwargs,
        )
        
    async def delete(
        self,
        url: HttpUrl,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute DELETE request."""
        return await self.client.request(
            method=HTTPMethod.DELETE,
            url=url,
            headers=headers,
            **kwargs,
        )


__all__ = [
    "APIConnectorService",
    "HTTPClient",
    "RequestBuilder",
    "ResponseHandler",
    "HTTPMethod",
    "RetryConfig",
    "RequestConfig",
    "APIResponse",
    "APIConnectorException",
    "RequestException",
    "ResponseException",
]