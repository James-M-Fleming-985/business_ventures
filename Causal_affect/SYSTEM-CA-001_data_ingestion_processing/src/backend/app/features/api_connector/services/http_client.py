import asyncio
import json
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field

from app.core.exceptions import APIException


class HTTPResponse(BaseModel):
    """HTTP response model"""
    status_code: int
    headers: Dict[str, str]
    content: Union[Dict[str, Any], str, bytes]
    elapsed_ms: float
    request_url: str


class HTTPClientConfig(BaseModel):
    """HTTP client configuration"""
    timeout: float = Field(default=30.0, ge=1.0)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, ge=0.1)
    verify_ssl: bool = True
    follow_redirects: bool = True
    max_redirects: int = Field(default=5, ge=1)


class HTTPClient:
    """Async HTTP client with retry logic and error handling"""
    
    def __init__(self, config: Optional[HTTPClientConfig] = None):
        self.config = config or HTTPClientConfig()
        self._client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        await self._ensure_client()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized"""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                follow_redirects=self.config.follow_redirects,
                max_redirects=self.config.max_redirects,
                verify=self.config.verify_ssl
            )
            
    async def close(self) -> None:
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
            
    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], bytes]] = None,
        auth: Optional[httpx.Auth] = None,
        **kwargs
    ) -> HTTPResponse:
        """Make HTTP request with retry logic"""
        await self._ensure_client()
        
        headers = headers or {}
        if json_data and 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
            
        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    data=data,
                    auth=auth,
                    **kwargs
                )
                
                content = await self._parse_response(response)
                
                return HTTPResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    content=content,
                    elapsed_ms=response.elapsed.total_seconds() * 1000,
                    request_url=str(response.request.url)
                )
                
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                raise APIException(
                    message=f"Request timeout after {self.config.timeout}s",
                    status_code=504,
                    details={"url": url, "method": method}
                )
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                    
                content = await self._parse_response(e.response)
                raise APIException(
                    message=f"HTTP {e.response.status_code}: {e.response.reason_phrase}",
                    status_code=e.response.status_code,
                    details={"url": url, "response": content}
                )
                
            except httpx.HTTPError as e:
                last_error = e
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                raise APIException(
                    message=f"HTTP error: {str(e)}",
                    status_code=500,
                    details={"url": url, "method": method}
                )
                
        raise APIException(
            message=f"Request failed after {self.config.max_retries} retries",
            status_code=500,
            details={"url": url, "last_error": str(last_error)}
        )
        
    async def _parse_response(
        self, 
        response: httpx.Response
    ) -> Union[Dict[str, Any], str, bytes]:
        """Parse response content based on content type"""
        content_type = response.headers.get('content-type', '')
        
        if 'application/json' in content_type:
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text
        elif 'text/' in content_type:
            return response.text
        else:
            return response.content
            
    async def get(
        self, 
        url: str, 
        **kwargs
    ) -> HTTPResponse:
        """Make GET request"""
        return await self.request('GET', url, **kwargs)
        
    async def post(
        self, 
        url: str, 
        **kwargs
    ) -> HTTPResponse:
        """Make POST request"""
        return await self.request('POST', url, **kwargs)
        
    async def put(
        self, 
        url: str, 
        **kwargs
    ) -> HTTPResponse:
        """Make PUT request"""
        return await self.request('PUT', url, **kwargs)
        
    async def patch(
        self, 
        url: str, 
        **kwargs
    ) -> HTTPResponse:
        """Make PATCH request"""
        return await self.request('PATCH', url, **kwargs)
        
    async def delete(
        self, 
        url: str, 
        **kwargs
    ) -> HTTPResponse:
        """Make DELETE request"""
        return await self.request('DELETE', url, **kwargs)
        

class HTTPClientFactory:
    """Factory for creating HTTP clients with specific configurations"""
    
    @staticmethod
    def create(
        base_url: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
        config: Optional[HTTPClientConfig] = None
    ) -> 'ConfiguredHTTPClient':
        """Create configured HTTP client"""
        return ConfiguredHTTPClient(
            base_url=base_url,
            default_headers=default_headers,
            config=config
        )
        

class ConfiguredHTTPClient(HTTPClient):
    """HTTP client with base URL and default headers"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
        config: Optional[HTTPClientConfig] = None
    ):
        super().__init__(config)
        self.base_url = base_url
        self.default_headers = default_headers or {}
        
    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> HTTPResponse:
        """Make request with base URL and default headers"""
        # Merge headers
        merged_headers = {**self.default_headers}
        if headers:
            merged_headers.update(headers)
            
        # Build full URL
        if self.base_url and not url.startswith(('http://', 'https://')):
            url = urljoin(self.base_url, url)
            
        return await super().request(
            method=method,
            url=url,
            headers=merged_headers,
            **kwargs
        )
