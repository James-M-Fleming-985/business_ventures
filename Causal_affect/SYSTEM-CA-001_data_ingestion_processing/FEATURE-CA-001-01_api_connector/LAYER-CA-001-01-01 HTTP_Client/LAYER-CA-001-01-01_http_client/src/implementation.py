```python
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import time


class HTTPClient:
    """HTTP client with connection pooling and concurrent request handling."""
    
    def __init__(self, timeout: int = 30, max_connections: int = 100):
        """
        Initialize HTTP client with connection pooling.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
            max_connections: Maximum number of concurrent connections (default: 100)
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_connections = max_connections
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        
    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
            return self._loop
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure session is created with connection pooling."""
        if self._session is None or self._session.closed:
            self._connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=self.max_connections,
                force_close=False,
                enable_cleanup_closed=True
            )
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=self.timeout
            )
        return self._session
    
    async def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Dict containing status_code and response data
        """
        session = await self._ensure_session()
        
        try:
            async with session.request(method, url, **kwargs) as response:
                data = await response.text()
                try:
                    json_data = await response.json()
                except:
                    json_data = data
                    
                return {
                    'status_code': response.status,
                    'data': json_data,
                    'headers': dict(response.headers),
                    'text': data
                }
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request timed out after {self.timeout.total} seconds")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        Synchronous wrapper for async request.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Dict containing status_code and response data
        """
        loop = self._get_loop()
        
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                self._request(method, url, **kwargs),
                loop
            )
            return future.result()
        else:
            return loop.run_until_complete(self._request(method, url, **kwargs))
    
    def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Make GET request.
        
        Args:
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Dict containing status_code and response data
        """
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Make POST request.
        
        Args:
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Dict containing status_code and response data
        """
        return self.request('POST', url, **kwargs)
    
    async def _concurrent_requests(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple requests concurrently.
        
        Args:
            requests: List of request dictionaries
            
        Returns:
            List of response dictionaries
        """
        tasks = []
        for req in requests:
            method = req.get('method', 'GET')
            url = req['url']
            kwargs = {k: v for k, v in req.items() if k not in ['method', 'url']}
            tasks.append(self._request(method, url, **kwargs))
        
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    def concurrent_requests(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple requests concurrently.
        
        Args:
            requests: List of request dictionaries containing:
                - url: Request URL (required)
                - method: HTTP method (default: GET)
                - Other kwargs for the request
            
        Returns:
            List of response dictionaries
        """
        loop = self._get_loop()
        
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                self._concurrent_requests(requests),
                loop
            )
            return future.result()
        else:
            return loop.run_until_complete(self._concurrent_requests(requests))
    
    def close(self):
        """Close the HTTP session and cleanup resources."""
        if self._session and not self._session.closed:
            loop = self._get_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self._session.close(), loop).result()
            else:
                loop.run_until_complete(self._session.close())
        
        if self._connector:
            self._connector.close()
            
        self._executor.shutdown(wait=True)
```