import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.config import settings
from core.exceptions import ExternalServiceError
from core.logging import logger


class MixpanelEvent(BaseModel):
    """Mixpanel event model."""
    
    model_config = ConfigDict(extra="allow")
    
    event: str = Field(..., description="Event name")
    properties: Dict[str, Any] = Field(default_factory=dict)
    distinct_id: Optional[str] = Field(None, description="User identifier")
    time: Optional[int] = Field(None, description="Unix timestamp")
    ip: Optional[str] = Field(None, description="IP address for geolocation")
    
    @field_validator("time", mode="before")
    @classmethod
    def validate_time(cls, v: Optional[Union[int, datetime]]) -> Optional[int]:
        if isinstance(v, datetime):
            return int(v.timestamp())
        return v


class MixpanelProfile(BaseModel):
    """Mixpanel user profile model."""
    
    model_config = ConfigDict(extra="allow")
    
    distinct_id: str = Field(..., description="User identifier")
    set: Optional[Dict[str, Any]] = Field(None, alias="$set")
    set_once: Optional[Dict[str, Any]] = Field(None, alias="$set_once")
    add: Optional[Dict[str, Union[int, float]]] = Field(None, alias="$add")
    append: Optional[Dict[str, Any]] = Field(None, alias="$append")
    union: Optional[Dict[str, List[Any]]] = Field(None, alias="$union")
    unset: Optional[List[str]] = Field(None, alias="$unset")
    delete: Optional[bool] = Field(None, alias="$delete")
    

class MixpanelClient:
    """Async Mixpanel client for event tracking and user profile management."""
    
    BASE_URL = "https://api.mixpanel.com"
    TRACK_ENDPOINT = "/track"
    ENGAGE_ENDPOINT = "/engage"
    BATCH_SIZE = 50
    
    def __init__(
        self,
        token: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        self.token = token or settings.MIXPANEL_TOKEN
        if not self.token:
            raise ValueError("Mixpanel token is required")
        
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
        self._batch_queue: List[Dict[str, Any]] = []
        self._profile_queue: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=httpx.Timeout(self.timeout),
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.flush()
        if self._client:
            await self._client.aclose()
    
    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        return self._client
    
    async def track(
        self,
        event_name: str,
        distinct_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """Track an event."""
        event = MixpanelEvent(
            event=event_name,
            distinct_id=distinct_id,
            properties=properties or {},
            **kwargs,
        )
        
        event_data = {
            "event": event.event,
            "properties": {
                **event.properties,
                "token": self.token,
                "distinct_id": event.distinct_id or "anonymous",
            },
        }
        
        if event.time:
            event_data["properties"]["time"] = event.time
        
        if event.ip:
            event_data["properties"]["ip"] = event.ip
        
        async with self._lock:
            self._batch_queue.append(event_data)
            
            if len(self._batch_queue) >= self.BATCH_SIZE:
                await self._flush_events()
    
    async def track_batch(
        self,
        events: List[Union[MixpanelEvent, Dict[str, Any]]]
    ) -> None:
        """Track multiple events in batch."""
        for event in events:
            if isinstance(event, dict):
                await self.track(**event)
            else:
                await self.track(
                    event_name=event.event,
                    distinct_id=event.distinct_id,
                    properties=event.properties,
                    time=event.time,
                    ip=event.ip,
                )
    
    async def update_profile(
        self,
        distinct_id: str,
        set_properties: Optional[Dict[str, Any]] = None,
        set_once: Optional[Dict[str, Any]] = None,
        add_properties: Optional[Dict[str, Union[int, float]]] = None,
        append_properties: Optional[Dict[str, Any]] = None,
        union_properties: Optional[Dict[str, List[Any]]] = None,
        unset_properties: Optional[List[str]] = None,
    ) -> None:
        """Update user profile."""
        profile = MixpanelProfile(
            distinct_id=distinct_id,
            set=set_properties,
            set_once=set_once,
            add=add_properties,
            append=append_properties,
            union=union_properties,
            unset=unset_properties,
        )
        
        profile_data = {
            "$token": self.token,
            "$distinct_id": profile.distinct_id,
        }
        
        # Add operations
        for field in ["set", "set_once", "add", "append", "union", "unset"]:
            value = getattr(profile, field)
            if value is not None:
                profile_data[f"${field}"] = value
        
        async with self._lock:
            self._profile_queue.append(profile_data)
            
            if len(self._profile_queue) >= self.BATCH_SIZE:
                await self._flush_profiles()
    
    async def delete_profile(self, distinct_id: str) -> None:
        """Delete user profile."""
        profile_data = {
            "$token": self.token,
            "$distinct_id": distinct_id,
            "$delete": "",
        }
        
        async with self._lock:
            self._profile_queue.append(profile_data)
            await self._flush_profiles()
    
    async def flush(self) -> None:
        """Flush all pending events and profile updates."""
        async with self._lock:
            if self._batch_queue:
                await self._flush_events()
            if self._profile_queue:
                await self._flush_profiles()
    
    async def _flush_events(self) -> None:
        """Send batched events to Mixpanel."""
        if not self._batch_queue:
            return
        
        events = self._batch_queue[:]
        self._batch_queue.clear()
        
        try:
            await self._send_request(
                endpoint=self.TRACK_ENDPOINT,
                data=events,
            )
        except Exception as e:
            logger.error(f"Failed to send events to Mixpanel: {e}")
            # Re-add events to queue for retry
            self._batch_queue.extend(events)
            raise
    
    async def _flush_profiles(self) -> None:
        """Send batched profile updates to Mixpanel."""
        if not self._profile_queue:
            return
        
        profiles = self._profile_queue[:]
        self._profile_queue.clear()
        
        try:
            await self._send_request(
                endpoint=self.ENGAGE_ENDPOINT,
                data=profiles,
            )
        except Exception as e:
            logger.error(f"Failed to send profiles to Mixpanel: {e}")
            # Re-add profiles to queue for retry
            self._profile_queue.extend(profiles)
            raise
    
    async def _send_request(
        self,
        endpoint: str,
        data: List[Dict[str, Any]],
    ) -> None:
        """Send request to Mixpanel API with retry logic."""
        if not data:
            return
        
        # Mixpanel expects base64-encoded JSON
        import base64
        
        json_data = json.dumps(data)
        encoded_data = base64.b64encode(json_data.encode()).decode()
        
        params = {
            "data": encoded_data,
            "verbose": "1",
        }
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    endpoint,
                    params=params,
                )
                
                response.raise_for_status()
                
                result = response.json()
                if result.get("status") != 1:
                    error_msg = result.get("error", "Unknown error")
                    raise ExternalServiceError(
                        f"Mixpanel API error: {error_msg}",
                        service="mixpanel",
                    )
                
                return
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise ExternalServiceError(
                    f"Mixpanel HTTP error: {e}",
                    service="mixpanel",
                    status_code=e.response.status_code,
                )
            except httpx.RequestError as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise ExternalServiceError(
                    f"Mixpanel request error: {e}",
                    service="mixpanel",
                )
            except Exception as e:
                raise ExternalServiceError(
                    f"Unexpected Mixpanel error: {e}",
                    service="mixpanel",
                )
    
    async def get_events(
        self,
        from_date: datetime,
        to_date: datetime,
        event: Optional[str] = None,
        where: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Query events from Mixpanel (requires appropriate API credentials)."""
        params = {
            "from_date": from_date.strftime("%Y-%m-%d"),
            "to_date": to_date.strftime("%Y-%m-%d"),
            "limit": limit,
        }
        
        if event:
            params["event"] = json.dumps([event])
        
        if where:
            params["where"] = where
        
        try:
            response = await self.client.get(
                "/api/2.0/export",
                params=params,
                auth=(self.token, ""),
            )
            response.raise_for_status()
            
            # Parse JSONL response
            events = []
            for line in response.text.strip().split("\n"):
                if line:
                    events.append(json.loads(line))
            
            return events
            
        except Exception as e:
            raise ExternalServiceError(
                f"Failed to query Mixpanel events: {e}",
                service="mixpanel",
            )


# Singleton instance
_mixpanel_client: Optional[MixpanelClient] = None


def get_mixpanel_client() -> MixpanelClient:
    """Get or create Mixpanel client instance."""
    global _mixpanel_client
    if _mixpanel_client is None:
        _mixpanel_client = MixpanelClient()
    return _mixpanel_client


# Common event helpers
async def track_user_action(
    user_id: str,
    action: str,
    properties: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> None:
    """Track user action with standard properties."""
    async with get_mixpanel_client() as client:
        await client.track(
            event_name=action,
            distinct_id=user_id,
            properties={
                **(properties or {}),
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs,
            },
        )


async def track_api_request(
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: float,
    user_id: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    """Track API request metrics."""
    async with get_mixpanel_client() as client:
        await client.track(
            event_name="api_request",
            distinct_id=user_id,
            properties={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "success": 200 <= status_code < 300,
                "error": error,
            },
        )
