from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.analytics_event import (
    AnalyticsEvent,
    AnalyticsEventCreate,
    AnalyticsEventUpdate,
    AnalyticsProvider,
)
from .schema import AnalyticsEventDB


class AnalyticsEventRepository:
    """Repository for analytics event database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, event: AnalyticsEventCreate) -> AnalyticsEvent:
        db_event = AnalyticsEventDB(
            event_name=event.event_name,
            category=event.category,
            provider=event.provider,
            user_id=event.user_id,
            session_id=event.session_id,
            properties=event.properties,
        )
        self.session.add(db_event)
        await self.session.commit()
        await self.session.refresh(db_event)
        return AnalyticsEvent.model_validate(db_event)
    
    async def create_batch(self, events: list[AnalyticsEventCreate]) -> list[AnalyticsEvent]:
        db_events = [
            AnalyticsEventDB(
                event_name=event.event_name,
                category=event.category,
                provider=event.provider,
                user_id=event.user_id,
                session_id=event.session_id,
                properties=event.properties,
            )
            for event in events
        ]
        self.session.add_all(db_events)
        await self.session.commit()
        
        for db_event in db_events:
            await self.session.refresh(db_event)
        
        return [AnalyticsEvent.model_validate(db_event) for db_event in db_events]
    
    async def get_by_id(self, event_id: UUID) -> Optional[AnalyticsEvent]:
        result = await self.session.execute(
            select(AnalyticsEventDB).where(AnalyticsEventDB.id == event_id)
        )
        db_event = result.scalar_one_or_none()
        return AnalyticsEvent.model_validate(db_event) if db_event else None
    
    async def get_pending_events(
        self,
        provider: AnalyticsProvider,
        limit: int = 100,
        max_retries: int = 3,
    ) -> list[AnalyticsEvent]:
        result = await self.session.execute(
            select(AnalyticsEventDB)
            .where(
                and_(
                    AnalyticsEventDB.provider == provider,
                    AnalyticsEventDB.status == "pending",
                    AnalyticsEventDB.retry_count < max_retries,
                )
            )
            .order_by(AnalyticsEventDB.created_at)
            .limit(limit)
        )
        return [AnalyticsEvent.model_validate(event) for event in result.scalars().all()]
    
    async def update(
        self,
        event_id: UUID,
        event_update: AnalyticsEventUpdate,
    ) -> Optional[AnalyticsEvent]:
        update_data = event_update.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_by_id(event_id)
        
        await self.session.execute(
            update(AnalyticsEventDB)
            .where(AnalyticsEventDB.id == event_id)
            .values(**update_data)
        )
        await self.session.commit()
        return await self.get_by_id(event_id)
    
    async def mark_as_sent(self, event_ids: list[UUID]) -> None:
        await self.session.execute(
            update(AnalyticsEventDB)
            .where(AnalyticsEventDB.id.in_(event_ids))
            .values(status="sent", sent_at=datetime.utcnow())
        )
        await self.session.commit()
    
    async def mark_as_failed(
        self,
        event_id: UUID,
        error_message: str,
    ) -> None:
        await self.session.execute(
            update(AnalyticsEventDB)
            .where(AnalyticsEventDB.id == event_id)
            .values(
                status="failed",
                error_message=error_message,
                retry_count=AnalyticsEventDB.retry_count + 1,
            )
        )
        await self.session.commit()
    
    async def retry_failed_events(self, max_retries: int = 3) -> int:
        result = await self.session.execute(
            update(AnalyticsEventDB)
            .where(
                and_(
                    AnalyticsEventDB.status == "failed",
                    AnalyticsEventDB.retry_count < max_retries,
                )
            )
            .values(status="pending")
            .returning(AnalyticsEventDB.id)
        )
        await self.session.commit()
        return len(result.all())
    
    async def get_events_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[AnalyticsEvent]:
        query = select(AnalyticsEventDB).where(AnalyticsEventDB.user_id == user_id)
        
        if start_date:
            query = query.where(AnalyticsEventDB.created_at >= start_date)
        if end_date:
            query = query.where(AnalyticsEventDB.created_at <= end_date)
        
        query = query.order_by(AnalyticsEventDB.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return [AnalyticsEvent.model_validate(event) for event in result.scalars().all()]
    
    async def get_event_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, any]:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Total events
        total_query = select(func.count(AnalyticsEventDB.id)).where(
            and_(
                AnalyticsEventDB.created_at >= start_date,
                AnalyticsEventDB.created_at <= end_date,
            )
        )
        total_result = await self.session.execute(total_query)
        total_events = total_result.scalar()
        
        # Events by status
        status_query = (
            select(
                AnalyticsEventDB.status,
                func.count(AnalyticsEventDB.id).label("count"),
            )
            .where(
                and_(
                    AnalyticsEventDB.created_at >= start_date,
                    AnalyticsEventDB.created_at <= end_date,
                )
            )
            .group_by(AnalyticsEventDB.status)
        )
        status_result = await self.session.execute(status_query)
        events_by_status = {row.status: row.count for row in status_result}
        
        # Events by provider
        provider_query = (
            select(
                AnalyticsEventDB.provider,
                func.count(AnalyticsEventDB.id).label("count"),
            )
            .where(
                and_(
                    AnalyticsEventDB.created_at >= start_date,
                    AnalyticsEventDB.created_at <= end_date,
                )
            )
            .group_by(AnalyticsEventDB.provider)
        )
        provider_result = await self.session.execute(provider_query)
        events_by_provider = {row.provider: row.count for row in provider_result}
        
        return {
            "total_events": total_events,
            "events_by_status": events_by_status,
            "events_by_provider": events_by_provider,
            "start_date": start_date,
            "end_date": end_date,
        }
    
    async def cleanup_old_events(self, days: int = 90) -> int:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(AnalyticsEventDB.id).where(
                and_(
                    AnalyticsEventDB.created_at < cutoff_date,
                    AnalyticsEventDB.status == "sent",
                )
            )
        )
        event_ids = [row[0] for row in result.all()]
        
        if event_ids:
            await self.session.execute(
                AnalyticsEventDB.__table__.delete().where(
                    AnalyticsEventDB.id.in_(event_ids)
                )
            )
            await self.session.commit()
        
        return len(event_ids)