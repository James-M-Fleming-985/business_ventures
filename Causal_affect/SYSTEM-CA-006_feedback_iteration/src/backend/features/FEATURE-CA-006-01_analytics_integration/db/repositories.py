"""Repository for analytics events database operations."""

from typing import Optional, Sequence
from datetime import datetime, timedelta
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from features.FEATURE-CA-006-01_analytics_integration.db.schema import AnalyticsEventDB
from features.FEATURE-CA-006-01_analytics_integration.models.analytics_event import (
    AnalyticsEventCreate,
    AnalyticsProvider,
)


class AnalyticsEventRepository:
    """Repository for analytics event database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(self, event: AnalyticsEventCreate) -> AnalyticsEventDB:
        """Create a new analytics event."""
        db_event = AnalyticsEventDB(
            user_id=event.user_id,
            event_name=event.event_name,
            event_params=event.event_params,
            user_properties=event.user_properties,
            provider=event.provider.value if isinstance(event.provider, AnalyticsProvider) else event.provider,
            session_id=event.session_id,
        )
        self.session.add(db_event)
        await self.session.commit()
        await self.session.refresh(db_event)
        return db_event

    async def get_event_by_id(self, event_id: int) -> Optional[AnalyticsEventDB]:
        """Get an event by ID."""
        stmt = select(AnalyticsEventDB).where(AnalyticsEventDB.id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_events_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AnalyticsEventDB]:
        """Get events for a specific user."""
        stmt = (
            select(AnalyticsEventDB)
            .where(AnalyticsEventDB.user_id == user_id)
            .order_by(desc(AnalyticsEventDB.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_pending_events(
        self,
        provider: Optional[str] = None,
        limit: int = 100,
    ) -> Sequence[AnalyticsEventDB]:
        """Get events that haven't been sent to providers yet."""
        conditions = []
        
        if provider == "google_analytics":
            conditions.append(AnalyticsEventDB.sent_to_ga == False)
        elif provider == "mixpanel":
            conditions.append(AnalyticsEventDB.sent_to_mixpanel == False)
        else:
            conditions.append(
                and_(
                    AnalyticsEventDB.sent_to_ga == False,
                    AnalyticsEventDB.sent_to_mixpanel == False,
                )
            )

        stmt = (
            select(AnalyticsEventDB)
            .where(and_(*conditions))
            .order_by(AnalyticsEventDB.created_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_sent_to_ga(self, event_id: int, success: bool = True, error_message: Optional[str] = None) -> None:
        """Mark event as sent to Google Analytics."""
        stmt = select(AnalyticsEventDB).where(AnalyticsEventDB.id == event_id)
        result = await self.session.execute(stmt)
        event = result.scalar_one_or_none()
        
        if event:
            event.sent_to_ga = success
            if error_message:
                event.error_message = error_message
            await self.session.commit()

    async def mark_sent_to_mixpanel(self, event_id: int, success: bool = True, error_message: Optional[str] = None) -> None:
        """Mark event as sent to Mixpanel."""
        stmt = select(AnalyticsEventDB).where(AnalyticsEventDB.id == event_id)
        result = await self.session.execute(stmt)
        event = result.scalar_one_or_none()
        
        if event:
            event.sent_to_mixpanel = success
            if error_message:
                event.error_message = error_message
            await self.session.commit()

    async def get_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        event_name: Optional[str] = None,
        limit: int = 1000,
    ) -> Sequence[AnalyticsEventDB]:
        """Get events within a date range."""
        conditions = [
            AnalyticsEventDB.created_at >= start_date,
            AnalyticsEventDB.created_at <= end_date,
        ]
        
        if event_name:
            conditions.append(AnalyticsEventDB.event_name == event_name)

        stmt = (
            select(AnalyticsEventDB)
            .where(and_(*conditions))
            .order_by(desc(AnalyticsEventDB.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_old_events(self, days: int = 90) -> int:
        """Delete events older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stmt = select(AnalyticsEventDB).where(AnalyticsEventDB.created_at < cutoff_date)
        result = await self.session.execute(stmt)
        events = result.scalars().all()
        
        count = len(events)
        for event in events:
            await self.session.delete(event)
        
        await self.session.commit()
        return count
