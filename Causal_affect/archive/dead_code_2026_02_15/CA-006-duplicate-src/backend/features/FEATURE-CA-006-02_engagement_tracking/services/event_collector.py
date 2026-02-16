from datetime import datetime
from typing import Dict, Any, Optional, List
import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from ..models.engagement_events import EngagementEventCreate, EngagementEventType
from ..db.models import EngagementEvent
from ..db.repositories import EngagementEventRepository
from ..exceptions import EventCollectionError, InvalidEventDataError


class EventCollectorService:
    """Collects and processes engagement events."""
    
    def __init__(
        self,
        db: AsyncSession,
        redis: Redis,
        event_repository: EngagementEventRepository
    ):
        self.db = db
        self.redis = redis
        self.event_repository = event_repository
        self.batch_size = 100
        self.batch_timeout = 5  # seconds
    
    async def collect_event(
        self,
        event_data: EngagementEventCreate,
        user_id: UUID,
        session_id: str
    ) -> EngagementEvent:
        """Collect and store a single engagement event."""
        try:
            # Validate event data
            if not self._validate_event_data(event_data):
                raise InvalidEventDataError(f"Invalid event data: {event_data}")
            
            # Add user and session info
            event_dict = event_data.model_dump()
            event_dict.update({
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow()
            })
            
            # Store in database
            event = await self.event_repository.create(event_dict)
            
            # Update cache
            await self._update_event_cache(event)
            
            # Trigger real-time processing if needed
            if event_data.event_type in [
                EngagementEventType.PURCHASE,
                EngagementEventType.FEEDBACK
            ]:
                await self._process_high_priority_event(event)
            
            return event
            
        except Exception as e:
            raise EventCollectionError(f"Failed to collect event: {str(e)}")
    
    async def collect_batch(
        self,
        events: List[Dict[str, Any]],
        user_id: UUID,
        session_id: str
    ) -> List[EngagementEvent]:
        """Collect multiple events in batch."""
        collected_events = []
        
        for event_data in events:
            try:
                event = EngagementEventCreate(**event_data)
                collected = await self.collect_event(event, user_id, session_id)
                collected_events.append(collected)
            except Exception as e:
                # Log error but continue processing other events
                continue
        
        return collected_events
    
    async def get_user_events(
        self,
        user_id: UUID,
        event_type: Optional[EngagementEventType] = None,
        limit: int = 100
    ) -> List[EngagementEvent]:
        """Retrieve events for a specific user."""
        # Check cache first
        cache_key = f"user_events:{user_id}:{event_type or 'all'}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # Query database
        filters = {"user_id": user_id}
        if event_type:
            filters["event_type"] = event_type
        
        events = await self.event_repository.get_many(
            filters=filters,
            limit=limit,
            order_by="timestamp"
        )
        
        # Update cache
        await self.redis.setex(
            cache_key,
            300,  # 5 minutes TTL
            json.dumps([e.model_dump() for e in events], default=str)
        )
        
        return events
    
    async def get_event_stats(
        self,
        user_id: Optional[UUID] = None,
        event_type: Optional[EngagementEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get aggregated event statistics."""
        stats = await self.event_repository.get_event_stats(
            user_id=user_id,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "total_events": stats.get("count", 0),
            "events_by_type": stats.get("by_type", {}),
            "avg_events_per_session": stats.get("avg_per_session", 0),
            "most_common_events": stats.get("most_common", [])
        }
    
    def _validate_event_data(self, event_data: EngagementEventCreate) -> bool:
        """Validate event data structure and content."""
        if not event_data.event_type:
            return False
        
        # Validate metadata based on event type
        if event_data.event_type == EngagementEventType.PAGE_VIEW:
            return "url" in event_data.metadata
        elif event_data.event_type == EngagementEventType.CLICK:
            return "element_id" in event_data.metadata
        elif event_data.event_type == EngagementEventType.SCROLL:
            return "percentage" in event_data.metadata
        
        return True
    
    async def _update_event_cache(self, event: EngagementEvent) -> None:
        """Update Redis cache with new event data."""
        # Update user event count
        count_key = f"event_count:{event.user_id}:{event.event_type}"
        await self.redis.incr(count_key)
        await self.redis.expire(count_key, 3600)  # 1 hour TTL
        
        # Update recent events list
        recent_key = f"recent_events:{event.user_id}"
        await self.redis.lpush(recent_key, event.id)
        await self.redis.ltrim(recent_key, 0, 99)  # Keep last 100
        await self.redis.expire(recent_key, 3600)
    
    async def _process_high_priority_event(self, event: EngagementEvent) -> None:
        """Process high-priority events for real-time actions."""
        # Publish to Redis pub/sub for real-time processing
        channel = f"engagement:priority:{event.event_type}"
        await self.redis.publish(
            channel,
            json.dumps({
                "event_id": str(event.id),
                "user_id": str(event.user_id),
                "session_id": event.session_id,
                "metadata": event.metadata
            })
        )
