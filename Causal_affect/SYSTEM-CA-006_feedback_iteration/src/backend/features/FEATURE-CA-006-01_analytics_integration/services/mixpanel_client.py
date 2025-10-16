"""Mixpanel client implementation."""

import httpx
import json
import base64
from typing import Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MixpanelError(Exception):
    """Mixpanel client error."""
    pass


class MixpanelClient:
    """Client for sending events to Mixpanel."""

    def __init__(self, api_key: str, project_token: str):
        self.api_key = api_key
        self.project_token = project_token
        self.track_url = "https://api.mixpanel.com/track"
        self.engage_url = "https://api.mixpanel.com/engage"
        self.client = httpx.AsyncClient(timeout=10.0)

    async def track_event(
        self,
        distinct_id: str,
        event_name: str,
        properties: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Track an event in Mixpanel.
        
        Args:
            distinct_id: Unique user identifier
            event_name: Name of the event
            properties: Event properties
            
        Returns:
            True if successful
        """
        event_data = {
            "event": event_name,
            "properties": {
                "distinct_id": distinct_id,
                "token": self.project_token,
                "time": int(datetime.utcnow().timestamp()),
                **(properties or {}),
            },
        }

        try:
            response = await self.client.post(
                self.track_url,
                params={"data": base64.b64encode(json.dumps([event_data]).encode()).decode()},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != 1:
                raise MixpanelError(f"Mixpanel returned error status: {result}")
            
            logger.info(f"Event '{event_name}' tracked in Mixpanel for user {distinct_id}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to track event in Mixpanel: {e}")
            raise MixpanelError(f"Failed to track event: {e}") from e

    async def set_user_properties(
        self,
        distinct_id: str,
        properties: dict[str, Any],
    ) -> bool:
        """Set user properties in Mixpanel."""
        engage_data = {
            "$token": self.project_token,
            "$distinct_id": distinct_id,
            "$set": properties,
        }

        try:
            response = await self.client.post(
                self.engage_url,
                params={"data": base64.b64encode(json.dumps([engage_data]).encode()).decode()},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != 1:
                raise MixpanelError(f"Mixpanel returned error status: {result}")
            
            logger.info(f"User properties set in Mixpanel for user {distinct_id}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to set user properties in Mixpanel: {e}")
            raise MixpanelError(f"Failed to set user properties: {e}") from e

    async def track_batch_events(
        self,
        events: list[dict[str, Any]],
    ) -> bool:
        """Track multiple events in a single request."""
        formatted_events = []
        for event in events:
            formatted_events.append({
                "event": event["event_name"],
                "properties": {
                    "distinct_id": event["distinct_id"],
                    "token": self.project_token,
                    "time": int(event.get("timestamp", datetime.utcnow()).timestamp()),
                    **event.get("properties", {}),
                },
            })

        try:
            response = await self.client.post(
                self.track_url,
                params={"data": base64.b64encode(json.dumps(formatted_events).encode()).decode()},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != 1:
                raise MixpanelError(f"Mixpanel returned error status: {result}")
            
            logger.info(f"Batch of {len(events)} events tracked in Mixpanel")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to track batch events in Mixpanel: {e}")
            raise MixpanelError(f"Failed to track batch events: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
