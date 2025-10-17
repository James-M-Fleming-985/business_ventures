"""Google Analytics client implementation."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from enum import Enum

import httpx
from pydantic import BaseModel, Field, validator
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Supported GA4 event types."""
    PAGE_VIEW = "page_view"
    USER_ENGAGEMENT = "user_engagement"
    SCROLL = "scroll"
    CLICK = "click"
    FILE_DOWNLOAD = "file_download"
    FORM_SUBMIT = "form_submit"
    VIDEO_START = "video_start"
    VIDEO_PROGRESS = "video_progress"
    VIDEO_COMPLETE = "video_complete"
    SEARCH = "search"
    PURCHASE = "purchase"
    ADD_TO_CART = "add_to_cart"
    CUSTOM = "custom_event"


class AnalyticsEvent(BaseModel):
    """Analytics event model."""
    name: str = Field(..., description="Event name")
    params: Dict[str, Any] = Field(default_factory=dict, description="Event parameters")
    user_id: Optional[str] = Field(None, description="User identifier")
    timestamp_micros: Optional[int] = Field(None, description="Event timestamp in microseconds")
    
    @validator("name")
    def validate_name(cls, v: str) -> str:
        if not v or len(v) > 40:
            raise ValueError("Event name must be between 1 and 40 characters")
        return v
    
    @validator("params")
    def validate_params(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if len(v) > 25:
            raise ValueError("Maximum 25 parameters allowed per event")
        return v


class UserProperty(BaseModel):
    """User property model."""
    name: str = Field(..., description="Property name")
    value: Union[str, int, float, bool] = Field(..., description="Property value")
    
    @validator("name")
    def validate_name(cls, v: str) -> str:
        if not v or len(v) > 24:
            raise ValueError("Property name must be between 1 and 24 characters")
        return v


class AnalyticsBatch(BaseModel):
    """Batch of analytics data."""
    client_id: str = Field(..., description="Client identifier")
    events: List[AnalyticsEvent] = Field(default_factory=list)
    user_properties: Dict[str, Any] = Field(default_factory=dict)
    timestamp_micros: Optional[int] = Field(None)
    
    @validator("events")
    def validate_events(cls, v: List[AnalyticsEvent]) -> List[AnalyticsEvent]:
        if len(v) > 25:
            raise ValueError("Maximum 25 events allowed per batch")
        return v


class GoogleAnalyticsConfig(BaseModel):
    """Google Analytics configuration."""
    measurement_id: str = Field(..., description="GA4 Measurement ID")
    api_secret: str = Field(..., description="GA4 API Secret")
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    batch_size: int = Field(default=25, description="Maximum events per batch")


class GoogleAnalyticsException(Exception):
    """Base exception for Google Analytics errors."""
    pass


class GoogleAnalyticsClient:
    """Google Analytics 4 client for event tracking."""
    
    BASE_URL = "https://www.google-analytics.com"
    DEBUG_URL = "https://www.google-analytics.com/debug"
    MP_VERSION = "2"
    
    def __init__(self, config: GoogleAnalyticsConfig) -> None:
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._event_queue: List[AnalyticsEvent] = []
        self._queue_lock = asyncio.Lock()
    
    async def __aenter__(self) -> "GoogleAnalyticsClient":
        await self.connect()
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        await self.disconnect()
    
    async def connect(self) -> None:
        """Initialize HTTP client."""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={"User-Agent": "GoogleAnalyticsClient/1.0"}
            )
    
    async def disconnect(self) -> None:
        """Close HTTP client and flush pending events."""
        if self._event_queue:
            await self.flush()
        
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def _send_request(
        self,
        endpoint: str,
        payload: Dict[str, Any]
    ) -> httpx.Response:
        """Send request to GA4 API with retry logic."""
        if not self._client:
            await self.connect()
        
        url = f"{self.BASE_URL}/{endpoint}"
        if self.config.debug_mode:
            url = f"{self.DEBUG_URL}/{endpoint}"
        
        params = {
            "measurement_id": self.config.measurement_id,
            "api_secret": self.config.api_secret
        }
        
        response = await self._client.post(
            url,
            params=params,
            json=payload
        )
        
        if self.config.debug_mode:
            logger.debug(f"GA4 Debug Response: {response.json()}")
        
        response.raise_for_status()
        return response
    
    async def track_event(
        self,
        event_name: str,
        client_id: str,
        event_params: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        user_properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track a single event."""
        event = AnalyticsEvent(
            name=event_name,
            params=event_params or {},
            user_id=user_id,
            timestamp_micros=int(datetime.now().timestamp() * 1_000_000)
        )
        
        batch = AnalyticsBatch(
            client_id=client_id,
            events=[event],
            user_properties=user_properties or {}
        )
        
        await self._send_batch(batch)
    
    async def track_events(
        self,
        events: List[AnalyticsEvent],
        client_id: str,
        user_properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track multiple events in a batch."""
        for i in range(0, len(events), self.config.batch_size):
            batch_events = events[i:i + self.config.batch_size]
            batch = AnalyticsBatch(
                client_id=client_id,
                events=batch_events,
                user_properties=user_properties or {}
            )
            await self._send_batch(batch)
    
    async def add_to_queue(
        self,
        event_name: str,
        client_id: str,
        event_params: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Add event to queue for batch processing."""
        event = AnalyticsEvent(
            name=event_name,
            params=event_params or {},
            user_id=user_id,
            timestamp_micros=int(datetime.now().timestamp() * 1_000_000)
        )
        
        async with self._queue_lock:
            self._event_queue.append(event)
            
            if len(self._event_queue) >= self.config.batch_size:
                await self.flush()
    
    async def flush(self) -> None:
        """Flush all queued events."""
        async with self._queue_lock:
            if not self._event_queue:
                return
            
            events_to_send = self._event_queue[:]
            self._event_queue.clear()
        
        # Group events by client_id if needed
        # For simplicity, assuming single client_id per flush
        # In production, you'd want to group by client_id
        if events_to_send:
            await self.track_events(
                events=events_to_send,
                client_id="default_client"  # Should be passed or stored
            )
    
    async def _send_batch(self, batch: AnalyticsBatch) -> None:
        """Send a batch of events to GA4."""
        payload = {
            "client_id": batch.client_id,
            "events": [
                {
                    "name": event.name,
                    "params": event.params,
                    **({
                        "timestamp_micros": str(event.timestamp_micros)
                    } if event.timestamp_micros else {})
                }
                for event in batch.events
            ]
        }
        
        if batch.user_properties:
            payload["user_properties"] = batch.user_properties
        
        if batch.timestamp_micros:
            payload["timestamp_micros"] = str(batch.timestamp_micros)
        
        try:
            await self._send_request("mp/collect", payload)
            logger.info(
                f"Successfully sent {len(batch.events)} events to GA4"
            )
        except httpx.HTTPError as e:
            logger.error(f"Failed to send events to GA4: {e}")
            raise GoogleAnalyticsException(
                f"Failed to send analytics data: {str(e)}"
            ) from e
    
    async def track_page_view(
        self,
        client_id: str,
        page_location: str,
        page_title: Optional[str] = None,
        user_id: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track a page view event."""
        params = {
            "page_location": page_location,
            "page_title": page_title or "",
            **(additional_params or {})
        }
        
        await self.track_event(
            event_name=EventType.PAGE_VIEW,
            client_id=client_id,
            event_params=params,
            user_id=user_id
        )
    
    async def track_user_engagement(
        self,
        client_id: str,
        engagement_time_msec: int,
        user_id: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track user engagement event."""
        params = {
            "engagement_time_msec": engagement_time_msec,
            **(additional_params or {})
        }
        
        await self.track_event(
            event_name=EventType.USER_ENGAGEMENT,
            client_id=client_id,
            event_params=params,
            user_id=user_id
        )
    
    async def track_search(
        self,
        client_id: str,
        search_term: str,
        user_id: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track search event."""
        params = {
            "search_term": search_term,
            **(additional_params or {})
        }
        
        await self.track_event(
            event_name=EventType.SEARCH,
            client_id=client_id,
            event_params=params,
            user_id=user_id
        )
    
    async def track_custom_event(
        self,
        client_id: str,
        event_name: str,
        event_params: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        user_properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track a custom event with any name and parameters."""
        await self.track_event(
            event_name=event_name,
            client_id=client_id,
            event_params=event_params,
            user_id=user_id,
            user_properties=user_properties
        )
    
    async def validate_event(
        self,
        event: AnalyticsEvent,
        client_id: str
    ) -> Dict[str, Any]:
        """Validate event using GA4 debug endpoint."""
        if not self.config.debug_mode:
            raise GoogleAnalyticsException(
                "Debug mode must be enabled to validate events"
            )
        
        batch = AnalyticsBatch(
            client_id=client_id,
            events=[event]
        )
        
        response = await self._send_request("mp/collect", batch.dict())
        return response.json()
