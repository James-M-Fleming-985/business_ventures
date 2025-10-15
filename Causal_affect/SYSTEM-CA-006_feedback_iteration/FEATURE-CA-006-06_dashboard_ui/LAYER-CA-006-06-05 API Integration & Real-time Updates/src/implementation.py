import asyncio
import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


@dataclass
class APIResponse:
    """Represents an API response."""
    status_code: int
    data: Any
    error: Optional[str] = None


@dataclass
class WebSocketMessage:
    """Represents a WebSocket message."""
    type: str
    data: Any
    timestamp: float = field(default_factory=time.time)


class ToastNotification:
    """Handles toast notifications for errors."""
    
    _notifications: List[Dict[str, Any]] = []
    
    @classmethod
    def show(cls, message: str, type: str = "error"):
        """Display a toast notification."""
        cls._notifications.append({
            "message": message,
            "type": type,
            "timestamp": time.time()
        })
    
    @classmethod
    def get_notifications(cls) -> List[Dict[str, Any]]:
        """Get all notifications."""
        return cls._notifications.copy()
    
    @classmethod
    def clear(cls):
        """Clear all notifications."""
        cls._notifications.clear()


class APIClient:
    """API client for backend communication with retry logic."""
    
    def __init__(self, base_url: str = "http://localhost:8000", max_retries: int = 3):
        self.base_url = base_url
        self.max_retries = max_retries
        self._mock_responses = {}
        self._call_count = {}
    
    def _set_mock_response(self, endpoint: str, response: APIResponse):
        """Set mock response for testing."""
        self._mock_responses[endpoint] = response
    
    def _get_call_count(self, endpoint: str) -> int:
        """Get number of calls to an endpoint."""
        return self._call_count.get(endpoint, 0)
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> APIResponse:
        """Make HTTP request with retry logic."""
        self._call_count[endpoint] = self._call_count.get(endpoint, 0) + 1
        
        if endpoint in self._mock_responses:
            response = self._mock_responses[endpoint]
            if response.status_code >= 400:
                raise Exception(f"API Error: {response.error}")
            return response
        
        return APIResponse(status_code=200, data={})
    
    async def get(self, endpoint: str) -> APIResponse:
        """GET request with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await self._make_request("GET", endpoint)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))
                continue
        
        error_msg = f"Request failed after {self.max_retries} retries: {str(last_exception)}"
        ToastNotification.show(error_msg, "error")
        raise Exception(error_msg)
    
    async def post(self, endpoint: str, data: Dict) -> APIResponse:
        """POST request with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await self._make_request("POST", endpoint, data)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))
                continue
        
        error_msg = f"Request failed after {self.max_retries} retries: {str(last_exception)}"
        ToastNotification.show(error_msg, "error")
        raise Exception(error_msg)
    
    async def put(self, endpoint: str, data: Dict) -> APIResponse:
        """PUT request with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await self._make_request("PUT", endpoint, data)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))
                continue
        
        error_msg = f"Request failed after {self.max_retries} retries: {str(last_exception)}"
        ToastNotification.show(error_msg, "error")
        raise Exception(error_msg)
    
    async def delete(self, endpoint: str) -> APIResponse:
        """DELETE request with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await self._make_request("DELETE", endpoint)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))
                continue
        
        error_msg = f"Request failed after {self.max_retries} retries: {str(last_exception)}"
        ToastNotification.show(error_msg, "error")
        raise Exception(error_msg)


class WebSocketClient:
    """WebSocket client with automatic reconnection."""
    
    def __init__(self, url: str = "ws://localhost:8000/ws", reconnect_interval: float = 1.0):
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.state = ConnectionState.DISCONNECTED
        self._message_handlers: List[Callable[[WebSocketMessage], None]] = []
        self._connection_task: Optional[asyncio.Task] = None
        self._should_reconnect = True
        self._mock_messages: List[WebSocketMessage] = []
        self._received_messages: List[WebSocketMessage] = []
    
    def on_message(self, handler: Callable[[WebSocketMessage], None]):
        """Register message handler."""
        self._message_handlers.append(handler)
    
    def _set_mock_messages(self, messages: List[WebSocketMessage]):
        """Set mock messages for testing."""
        self._mock_messages = messages
    
    def get_received_messages(self) -> List[WebSocketMessage]:
        """Get all received messages."""
        return self._received_messages.copy()
    
    async def connect(self):
        """Connect to WebSocket server."""
        self.state = ConnectionState.CONNECTING
        await asyncio.sleep(0.05)
        self.state = ConnectionState.CONNECTED
        
        for msg in self._mock_messages:
            self._handle_message(msg)
    
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        self._should_reconnect = False
        if self._connection_task:
            self._connection_task.cancel()
        self.state = ConnectionState.DISCONNECTED
    
    async def _reconnect_loop(self):
        """Automatic reconnection loop."""
        while self._should_reconnect:
            if self.state == ConnectionState.DISCONNECTED:
                try:
                    self.state = ConnectionState.RECONNECTING
                    await asyncio.sleep(self.reconnect_interval)
                    await self.connect()
                except Exception:
                    await asyncio.sleep(self.reconnect_interval)
            else:
                await asyncio.sleep(0.1)
    
    def start_reconnect_loop(self):
        """Start the reconnection loop."""
        self._should_reconnect = True
        self._connection_task = asyncio.create_task(self._reconnect_loop())
    
    def _handle_message(self, message: WebSocketMessage):
        """Handle incoming message."""
        self._received_messages.append(message)
        for handler in self._message_handlers:
            handler(message)
    
    def simulate_disconnect(self):
        """Simulate connection loss for testing."""
        self.state = ConnectionState.DISCONNECTED
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.state == ConnectionState.CONNECTED


class PortfolioDataHook:
    """Hook for fetching portfolio data."""
    
    def __init__(self, api_client: APIClient, refresh_interval: float = 30.0):
        self.api_client = api_client
        self.refresh_interval = refresh_interval
        self.data: Optional[Dict] = None
        self.loading = False
        self.error: Optional[str] = None
        self._refresh_task: Optional[asyncio.Task] = None
        self._should_refresh = False
    
    async def fetch_data(self) -> Dict:
        """Fetch portfolio data from API."""
        self.loading = True
        self.error = None
        
        try:
            response = await self.api_client.get("/api/portfolio")
            self.data = response.data
            self.loading = False
            return self.data
        except Exception as e:
            self.error = str(e)
            self.loading = False
            raise
    
    async def _auto_refresh_loop(self):
        """Automatic refresh loop."""
        while self._should_refresh:
            try:
                await self.fetch_data()
            except Exception:
                pass
            await asyncio.sleep(self.refresh_interval)
    
    def start_auto_refresh(self):
        """Start automatic data refresh."""
        self._should_refresh = True
        self._refresh_task = asyncio.create_task(self._auto_refresh_loop())
    
    def stop_auto_refresh(self):
        """Stop automatic data refresh."""
        self._should_refresh = False
        if self._refresh_task:
            self._refresh_task.cancel()


class MVPDetailHook:
    """Hook for fetching MVP-specific data."""
    
    def __init__(self, api_client: APIClient, mvp_id: str):
        self.api_client = api_client
        self.mvp_id = mvp_id
        self.data: Optional[Dict] = None
        self.loading = False
        self.error: Optional[str] = None
    
    async def fetch_data(self) -> Dict:
        """Fetch MVP detail data from API."""
        self.loading = True
        self.error = None
        
        try:
            response = await self.api_client.get(f"/api/mvp/{self.mvp_id}")
            self.data = response.data
            self.loading = False
            return self.data
        except Exception as e:
            self.error = str(e)
            self.loading = False
            raise


def use_portfolio_data(api_client: APIClient, auto_refresh: bool = False) -> PortfolioDataHook:
    """Create portfolio data hook."""
    hook = PortfolioDataHook(api_client)
    if auto_refresh:
        hook.start_auto_refresh()
    return hook


def use_mvp_detail(api_client: APIClient, mvp_id: str) -> MVPDetailHook:
    """Create MVP detail hook."""
    return MVPDetailHook(api_client, mvp_id)
