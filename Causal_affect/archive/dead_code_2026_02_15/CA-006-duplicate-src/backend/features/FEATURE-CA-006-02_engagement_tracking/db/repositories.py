from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, and_, or_, desc, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import json

from .schema import (
    EngagementSession, EngagementEvent, EngagementMetrics, PageEngagement
)


class EngagementRepository:
    """Repository for engagement tracking operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_session(self, 
                           user_id: UUID,
                           session_id: str,
                           device_type: Optional[str] = None,
                           browser: Optional[str] = None,
                           ip_address: Optional[str] = None) -> EngagementSession:
        """Create new engagement session"""
        session = EngagementSession(
            user_id=user_id,
            session_id=session_id,
            device_type=device_type,
            browser=browser,
            ip_address=ip_address
        )
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session
    
    async def get_session(self, session_id: str) -> Optional[EngagementSession]:
        """Get session by ID"""
        result = await self.session.execute(
            select(EngagementSession).where(
                EngagementSession.session_id == session_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_active_session(self, 
                               user_id: UUID,
                               timeout_minutes: int = 30) -> Optional[EngagementSession]:
        """Get active session for user within timeout"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        result = await self.session.execute(
            select(EngagementSession).where(
                and_(
                    EngagementSession.user_id == user_id,
                    EngagementSession.is_active == True,
                    EngagementSession.last_activity_at > cutoff_time
                )
            ).order_by(desc(EngagementSession.last_activity_at))
        )
        return result.scalars().first()
    
    async def update_session_activity(self, 
                                    session_id: str,
                                    increment_views: bool = False,
                                    increment_interactions: bool = False) -> Optional[EngagementSession]:
        """Update session last activity and counters"""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        session.last_activity_at = datetime.utcnow()
        if increment_views:
            session.page_views += 1
        if increment_interactions:
            session.interactions += 1
        
        # Update duration
        if session.started_at:
            duration = (session.last_activity_at - session.started_at).total_seconds()
            session.duration_seconds = int(duration)
        
        await self.session.commit()
        await self.session.refresh(session)
        return session
    
    async def end_session(self, session_id: str) -> Optional[EngagementSession]:
        """End an active session"""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        session.is_active = False
        session.ended_at = datetime.utcnow()
        session.duration_seconds = int(
            (session.ended_at - session.started_at).total_seconds()
        )
        
        await self.session.commit()
        await self.session.refresh(session)
        return session
    
    async def end_inactive_sessions(self, timeout_minutes: int = 30) -> int:
        """End all inactive sessions past timeout"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        result = await self.session.execute(
            select(EngagementSession).where(
                and_(
                    EngagementSession.is_active == True,
                    EngagementSession.last_activity_at < cutoff_time
                )
            )
        )
        sessions = result.scalars().all()
        
        count = 0
        for session in sessions:
            session.is_active = False
            session.ended_at = cutoff_time
            session.duration_seconds = int(
                (session.ended_at - session.started_at).total_seconds()
            )
            count += 1
        
        if count > 0:
            await self.session.commit()
        return count
    
    async def create_event(self,
                         session_id: str,
                         user_id: UUID,
                         event_type: str,
                         event_name: str,
                         event_category: Optional[str] = None,
                         event_value: Optional[str] = None,
                         numeric_value: Optional[float] = None,
                         page_url: Optional[str] = None,
                         element_id: Optional[str] = None,
                         element_class: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> EngagementEvent:
        """Create engagement event"""
        event = EngagementEvent(
            session_id=session_id,
            user_id=user_id,
            event_type=event_type,
            event_name=event_name,
            event_category=event_category,
            event_value=event_value,
            numeric_value=numeric_value,
            page_url=page_url,
            element_id=element_id,
            element_class=element_class,
            metadata=json.dumps(metadata) if metadata else None
        )
        self.session.add(event)
        
        # Update session activity based on event type
        increment_views = event_type == "page_view"
        increment_interactions = event_type in ["click", "form_submit", "interaction"]
        await self.update_session_activity(
            session_id, 
            increment_views=increment_views,
            increment_interactions=increment_interactions
        )
        
        await self.session.commit()
        await self.session.refresh(event)
        return event
    
    async def get_user_events(self,
                            user_id: UUID,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            event_type: Optional[str] = None,
                            limit: int = 100) -> List[EngagementEvent]:
        """Get events for a user"""
        query = select(EngagementEvent).where(
            EngagementEvent.user_id == user_id
        )
        
        if start_date:
            query = query.where(EngagementEvent.timestamp >= start_date)
        if end_date:
            query = query.where(EngagementEvent.timestamp <= end_date)
        if event_type:
            query = query.where(EngagementEvent.event_type == event_type)
        
        query = query.order_by(desc(EngagementEvent.timestamp)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def calculate_user_metrics(self,
                                   user_id: UUID,
                                   start_date: datetime,
                                   end_date: datetime,
                                   metric_type: str = "daily") -> EngagementMetrics:
        """Calculate and store user engagement metrics"""
        # Get sessions in date range
        sessions_query = select(EngagementSession).where(
            and_(
                EngagementSession.user_id == user_id,
                EngagementSession.started_at >= start_date,
                EngagementSession.started_at < end_date
            )
        )
        result = await self.session.execute(sessions_query)
        sessions = result.scalars().all()
        
        # Calculate metrics
        total_sessions = len(sessions)
        total_duration = sum(s.duration_seconds for s in sessions)
        avg_duration = total_duration / total_sessions if total_sessions > 0 else 0
        total_page_views = sum(s.page_views for s in sessions)
        total_interactions = sum(s.interactions for s in sessions)
        
        # Calculate bounce rate (sessions with 1 or fewer page views)
        bounce_sessions = sum(1 for s in sessions if s.page_views <= 1)
        bounce_rate = bounce_sessions / total_sessions if total_sessions > 0 else 0
        
        # Get unique pages visited
        pages_query = select(distinct(EngagementEvent.page_url)).where(
            and_(
                EngagementEvent.user_id == user_id,
                EngagementEvent.timestamp >= start_date,
                EngagementEvent.timestamp < end_date,
                EngagementEvent.page_url.isnot(None)
            )
        )
        pages_result = await self.session.execute(pages_query)
        unique_pages = len(pages_result.scalars().all())
        
        # Get most visited page
        top_page_query = select(
            EngagementEvent.page_url,
            func.count(EngagementEvent.id).label('count')
        ).where(
            and_(
                EngagementEvent.user_id == user_id,
                EngagementEvent.timestamp >= start_date,
                EngagementEvent.timestamp < end_date,
                EngagementEvent.event_type == "page_view",
                EngagementEvent.page_url.isnot(None)
            )
        ).group_by(EngagementEvent.page_url).order_by(desc('count'))
        
        top_page_result = await self.session.execute(top_page_query)
        top_page_row = top_page_result.first()
        most_visited = top_page_row[0] if top_page_row else None
        
        # Calculate engagement score (0-100)
        engagement_score = min(100, (
            (total_sessions * 10) +
            (avg_duration / 60 * 5) +  # minutes * 5
            (total_interactions * 2) +
            (unique_pages * 3) +
            ((1 - bounce_rate) * 20)
        ))
        
        # Check if metrics already exist
        existing_query = select(EngagementMetrics).where(
            and_(
                EngagementMetrics.user_id == user_id,
                EngagementMetrics.metric_date == start_date,
                EngagementMetrics.metric_type == metric_type
            )
        )
        existing_result = await self.session.execute(existing_query)
        metrics = existing_result.scalar_one_or_none()
        
        if metrics:
            # Update existing
            metrics.total_sessions = total_sessions
            metrics.total_duration_seconds = total_duration
            metrics.avg_session_duration = avg_duration
            metrics.total_page_views = total_page_views
            metrics.total_interactions = total_interactions
            metrics.unique_pages_visited = unique_pages
            metrics.bounce_rate = bounce_rate
            metrics.engagement_score = engagement_score
            metrics.most_visited_page = most_visited
            metrics.updated_at = datetime.utcnow()
        else:
            # Create new
            metrics = EngagementMetrics(
                user_id=user_id,
                metric_date=start_date,
                metric_type=metric_type,
                total_sessions=total_sessions,
                total_duration_seconds=total_duration,
                avg_session_duration=avg_duration,
                total_page_views=total_page_views,
                total_interactions=total_interactions,
                unique_pages_visited=unique_pages,
                bounce_rate=bounce_rate,
                engagement_score=engagement_score,
                most_visited_page=most_visited
            )
            self.session.add(metrics)
        
        await self.session.commit()
        await self.session.refresh(metrics)
        return metrics
    
    async def get_user_metrics(self,
                             user_id: UUID,
                             metric_type: str = "daily",
                             limit: int = 30) -> List[EngagementMetrics]:
        """Get user engagement metrics"""
        query = select(EngagementMetrics).where(
            and_(
                EngagementMetrics.user_id == user_id,
                EngagementMetrics.metric_type == metric_type
            )
        ).order_by(desc(EngagementMetrics.metric_date)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_page_engagement(self,
                                   page_url: str,
                                   date: datetime) -> PageEngagement:
        """Update page engagement metrics"""
        # Get or create page engagement record
        existing_query = select(PageEngagement).where(
            and_(
                PageEngagement.page_url == page_url,
                PageEngagement.date == date.replace(hour=0, minute=0, second=0, microsecond=0)
            )
        )
        result = await self.session.execute(existing_query)
        page_metrics = result.scalar_one_or_none()
        
        # Calculate metrics from events
        events_query = select(EngagementEvent).where(
            and_(
                EngagementEvent.page_url == page_url,
                func.date(EngagementEvent.timestamp) == date.date()
            )
        )
        events_result = await self.session.execute(events_query)
        events = events_result.scalars().all()
        
        # Count views and unique visitors
        page_views = sum(1 for e in events if e.event_type == "page_view")
        unique_visitors = len(set(e.user_id for e in events))
        total_interactions = sum(1 for e in events if e.event_type != "page_view")
        
        if page_metrics:
            page_metrics.total_views = page_views
            page_metrics.unique_visitors = unique_visitors
            page_metrics.total_interactions = total_interactions
            page_metrics.updated_at = datetime.utcnow()
        else:
            page_metrics = PageEngagement(
                page_url=page_url,
                date=date.replace(hour=0, minute=0, second=0, microsecond=0),
                total_views=page_views,
                unique_visitors=unique_visitors,
                total_interactions=total_interactions
            )
            self.session.add(page_metrics)
        
        await self.session.commit()
        await self.session.refresh(page_metrics)
        return page_metrics