"""Google Analytics 4 client implementation."""

import httpx
from typing import Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GoogleAnalyticsError(Exception):
    """Google Analytics client error."""
    pass


class GoogleAnalyticsClient:
    """Client for sending events to Google Analytics 4."""

    def __init__(self, measurement_id: str, api_secret: str):
        self.measurement_id = measurement_id
        self.api_secret = api_secret
        self.base_url = "https://www.google-analytics.com/mp/collect"
        self.client = httpx.AsyncClient(timeout=10.0)

    async def send_event(
        self,
        client_id: str,
        event_name: str,
        event_params: Optional[dict[str, Any]] = None,
        user_properties: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Send event to Google Analytics.
        
        Args:
            client_id: Unique client identifier
            event_name: Name of the event
            event_params: Event parameters
            user_properties: User properties
            
        Returns:
            True if successful, False otherwise
        """
        payload = {
            "client_id": client_id,
            "events": [
                {
                    "name": event_name,
                    "params": event_params or {},
                }
            ],
        }

        if user_properties:
            payload["user_properties"] = user_properties

        try:
            response = await self.client.post(
                self.base_url,
                params={
                    "measurement_id": self.measurement_id,
                    "api_secret": self.api_secret,
                },
                json=payload,
            )
            response.raise_for_status()
            logger.info(f"Event '{event_name}' sent to Google Analytics for client {client_id}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send event to Google Analytics: {e}")
            raise GoogleAnalyticsError(f"Failed to send event: {e}") from e

    async def send_batch_events(
        self,
        client_id: str,
        events: list[dict[str, Any]],
        user_properties: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Send multiple events in a single request."""
        payload = {
            "client_id": client_id,
            "events": events,
        }

        if user_properties:
            payload["user_properties"] = user_properties

        try:
            response = await self.client.post(
                self.base_url,
                params={
                    "measurement_id": self.measurement_id,
                    "api_secret": self.api_secret,
                },
                json=payload,
            )
            response.raise_for_status()
            logger.info(f"Batch of {len(events)} events sent to Google Analytics")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send batch events to Google Analytics: {e}")
            raise GoogleAnalyticsError(f"Failed to send batch events: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
