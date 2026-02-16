from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from decimal import Decimal
import logging

from ..models.engagement import (
    EngagementMetrics,
    EngagementTrend,
    MetricType,
    TimeRange,
    EngagementSummary,
    ChannelMetrics,
    ContentMetrics,
    EngagementRate
)
from ..db.models import EngagementEvent, UserEngagement
from ..exceptions import MetricsCalculationError

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Service for calculating engagement metrics."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        
    async def calculate_user_metrics(
        self,
        user_id: str,
        time_range: TimeRange,
        metric_types: Optional[List[MetricType]] = None
    ) -> EngagementMetrics:
        """Calculate engagement metrics for a specific user."""
        try:
            start_date = self._get_start_date(time_range)
            
            # Fetch engagement events
            events = await self._fetch_user_events(user_id, start_date)
            
            # Calculate base metrics
            base_metrics = await self._calculate_base_metrics(events)
            
            # Calculate specific metrics if requested
            if metric_types:
                specific_metrics = await self._calculate_specific_metrics(
                    events, metric_types
                )
                base_metrics.update(specific_metrics)
            
            # Calculate trends
            trends = await self._calculate_trends(
                user_id, time_range, base_metrics
            )
            
            return EngagementMetrics(
                user_id=user_id,
                time_range=time_range,
                metrics=base_metrics,
                trends=trends,
                calculated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error calculating metrics for user {user_id}: {str(e)}")
            raise MetricsCalculationError(f"Failed to calculate metrics: {str(e)}")
    
    async def calculate_channel_metrics(
        self,
        channel: str,
        time_range: TimeRange
    ) -> ChannelMetrics:
        """Calculate engagement metrics for a specific channel."""
        start_date = self._get_start_date(time_range)
        
        # Fetch channel-specific events
        query = select(EngagementEvent).where(
            and_(
                EngagementEvent.channel == channel,
                EngagementEvent.timestamp >= start_date
            )
        )
        result = await self.db_session.execute(query)
        events = result.scalars().all()
        
        # Calculate channel metrics
        total_interactions = len(events)
        unique_users = len(set(e.user_id for e in events))
        
        # Group by event type
        event_breakdown = {}
        for event in events:
            event_breakdown[event.event_type] = event_breakdown.get(
                event.event_type, 0
            ) + 1
        
        # Calculate average engagement rate
        engagement_rate = await self._calculate_channel_engagement_rate(
            channel, start_date
        )
        
        return ChannelMetrics(
            channel=channel,
            time_range=time_range,
            total_interactions=total_interactions,
            unique_users=unique_users,
            engagement_rate=engagement_rate,
            event_breakdown=event_breakdown,
            calculated_at=datetime.utcnow()
        )
    
    async def calculate_content_metrics(
        self,
        content_id: str,
        content_type: str,
        time_range: TimeRange
    ) -> ContentMetrics:
        """Calculate engagement metrics for specific content."""
        start_date = self._get_start_date(time_range)
        
        # Fetch content-specific events
        query = select(EngagementEvent).where(
            and_(
                EngagementEvent.content_id == content_id,
                EngagementEvent.timestamp >= start_date
            )
        )
        result = await self.db_session.execute(query)
        events = result.scalars().all()
        
        # Calculate content metrics
        views = sum(1 for e in events if e.event_type == 'view')
        likes = sum(1 for e in events if e.event_type == 'like')
        shares = sum(1 for e in events if e.event_type == 'share')
        comments = sum(1 for e in events if e.event_type == 'comment')
        
        # Calculate engagement score
        engagement_score = self._calculate_content_engagement_score(
            views, likes, shares, comments
        )
        
        # Get unique engagers
        unique_engagers = len(set(e.user_id for e in events))
        
        return ContentMetrics(
            content_id=content_id,
            content_type=content_type,
            time_range=time_range,
            views=views,
            likes=likes,
            shares=shares,
            comments=comments,
            engagement_score=engagement_score,
            unique_engagers=unique_engagers,
            calculated_at=datetime.utcnow()
        )
    
    async def calculate_summary(
        self,
        time_range: TimeRange,
        filters: Optional[Dict[str, Any]] = None
    ) -> EngagementSummary:
        """Calculate overall engagement summary."""
        start_date = self._get_start_date(time_range)
        
        # Build query with filters
        query = select(EngagementEvent).where(
            EngagementEvent.timestamp >= start_date
        )
        
        if filters:
            if 'channel' in filters:
                query = query.where(EngagementEvent.channel == filters['channel'])
            if 'event_type' in filters:
                query = query.where(EngagementEvent.event_type == filters['event_type'])
        
        result = await self.db_session.execute(query)
        events = result.scalars().all()
        
        # Calculate summary metrics
        total_events = len(events)
        unique_users = len(set(e.user_id for e in events))
        
        # Group by channel
        channel_breakdown = {}
        for event in events:
            channel = event.channel
            if channel not in channel_breakdown:
                channel_breakdown[channel] = {
                    'count': 0,
                    'unique_users': set()
                }
            channel_breakdown[channel]['count'] += 1
            channel_breakdown[channel]['unique_users'].add(event.user_id)
        
        # Convert sets to counts
        for channel in channel_breakdown:
            channel_breakdown[channel]['unique_users'] = len(
                channel_breakdown[channel]['unique_users']
            )
        
        # Calculate average engagement per user
        avg_engagement_per_user = (
            float(total_events) / unique_users if unique_users > 0 else 0.0
        )
        
        # Get top engaged users
        top_users = await self._get_top_engaged_users(start_date, limit=10)
        
        return EngagementSummary(
            time_range=time_range,
            total_events=total_events,
            unique_users=unique_users,
            avg_engagement_per_user=avg_engagement_per_user,
            channel_breakdown=channel_breakdown,
            top_users=top_users,
            calculated_at=datetime.utcnow()
        )
    
    async def calculate_engagement_rate(
        self,
        numerator_events: List[str],
        denominator_events: List[str],
        time_range: TimeRange,
        group_by: Optional[str] = None
    ) -> Dict[str, EngagementRate]:
        """Calculate engagement rate based on custom event definitions."""
        start_date = self._get_start_date(time_range)
        
        # Fetch numerator events
        num_query = select(
            EngagementEvent.user_id,
            func.count(EngagementEvent.id).label('count')
        ).where(
            and_(
                EngagementEvent.event_type.in_(numerator_events),
                EngagementEvent.timestamp >= start_date
            )
        ).group_by(EngagementEvent.user_id)
        
        # Fetch denominator events
        denom_query = select(
            EngagementEvent.user_id,
            func.count(EngagementEvent.id).label('count')
        ).where(
            and_(
                EngagementEvent.event_type.in_(denominator_events),
                EngagementEvent.timestamp >= start_date
            )
        ).group_by(EngagementEvent.user_id)
        
        num_result = await self.db_session.execute(num_query)
        denom_result = await self.db_session.execute(denom_query)
        
        num_counts = {row.user_id: row.count for row in num_result}
        denom_counts = {row.user_id: row.count for row in denom_result}
        
        # Calculate rates
        rates = {}
        for user_id, denom_count in denom_counts.items():
            num_count = num_counts.get(user_id, 0)
            rate = float(num_count) / float(denom_count) if denom_count > 0 else 0.0
            
            rates[user_id] = EngagementRate(
                user_id=user_id,
                rate=rate,
                numerator_count=num_count,
                denominator_count=denom_count,
                time_range=time_range
            )
        
        return rates
    
    async def _fetch_user_events(
        self,
        user_id: str,
        start_date: datetime
    ) -> List[EngagementEvent]:
        """Fetch engagement events for a user."""
        query = select(EngagementEvent).where(
            and_(
                EngagementEvent.user_id == user_id,
                EngagementEvent.timestamp >= start_date
            )
        )
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def _calculate_base_metrics(
        self,
        events: List[EngagementEvent]
    ) -> Dict[str, Any]:
        """Calculate base engagement metrics."""
        metrics = {
            'total_events': len(events),
            'unique_days': len(set(e.timestamp.date() for e in events)),
            'event_types': {},
            'channels': {},
            'avg_daily_events': 0.0
        }
        
        # Count by event type
        for event in events:
            event_type = event.event_type
            metrics['event_types'][event_type] = metrics['event_types'].get(
                event_type, 0
            ) + 1
            
            channel = event.channel
            metrics['channels'][channel] = metrics['channels'].get(channel, 0) + 1
        
        # Calculate average daily events
        if metrics['unique_days'] > 0:
            metrics['avg_daily_events'] = (
                float(metrics['total_events']) / metrics['unique_days']
            )
        
        return metrics
    
    async def _calculate_specific_metrics(
        self,
        events: List[EngagementEvent],
        metric_types: List[MetricType]
    ) -> Dict[str, Any]:
        """Calculate specific requested metrics."""
        specific_metrics = {}
        
        for metric_type in metric_types:
            if metric_type == MetricType.CLICK_THROUGH_RATE:
                clicks = sum(1 for e in events if e.event_type == 'click')
                views = sum(1 for e in events if e.event_type == 'view')
                ctr = float(clicks) / views if views > 0 else 0.0
                specific_metrics['click_through_rate'] = ctr
                
            elif metric_type == MetricType.CONVERSION_RATE:
                conversions = sum(1 for e in events if e.event_type == 'conversion')
                total = len(events)
                cvr = float(conversions) / total if total > 0 else 0.0
                specific_metrics['conversion_rate'] = cvr
                
            elif metric_type == MetricType.ENGAGEMENT_SCORE:
                score = await self._calculate_engagement_score(events)
                specific_metrics['engagement_score'] = score
                
            elif metric_type == MetricType.RETENTION_RATE:
                retention = await self._calculate_retention_rate(events)
                specific_metrics['retention_rate'] = retention
        
        return specific_metrics
    
    async def _calculate_trends(
        self,
        user_id: str,
        time_range: TimeRange,
        current_metrics: Dict[str, Any]
    ) -> List[EngagementTrend]:
        """Calculate metric trends compared to previous period."""
        trends = []
        
        # Get previous period metrics
        previous_range = self._get_previous_time_range(time_range)
        previous_start = self._get_start_date(previous_range)
        previous_end = self._get_start_date(time_range)
        
        previous_events = await self._fetch_user_events_in_range(
            user_id, previous_start, previous_end
        )
        previous_metrics = await self._calculate_base_metrics(previous_events)
        
        # Calculate trends for key metrics
        for metric_name in ['total_events', 'avg_daily_events']:
            if metric_name in current_metrics and metric_name in previous_metrics:
                current_value = float(current_metrics[metric_name])
                previous_value = float(previous_metrics[metric_name])
                
                if previous_value > 0:
                    change_percentage = (
                        (current_value - previous_value) / previous_value * 100
                    )
                else:
                    change_percentage = 100.0 if current_value > 0 else 0.0
                
                trend = EngagementTrend(
                    metric_name=metric_name,
                    current_value=current_value,
                    previous_value=previous_value,
                    change_percentage=change_percentage,
                    trend_direction='up' if change_percentage > 0 else 
                                   'down' if change_percentage < 0 else 'stable'
                )
                trends.append(trend)
        
        return trends
    
    async def _calculate_channel_engagement_rate(
        self,
        channel: str,
        start_date: datetime
    ) -> float:
        """Calculate engagement rate for a channel."""
        # Get total interactions
        interaction_query = select(
            func.count(EngagementEvent.id)
        ).where(
            and_(
                EngagementEvent.channel == channel,
                EngagementEvent.timestamp >= start_date,
                EngagementEvent.event_type.in_(['like', 'comment', 'share'])
            )
        )
        
        # Get total views
        view_query = select(
            func.count(EngagementEvent.id)
        ).where(
            and_(
                EngagementEvent.channel == channel,
                EngagementEvent.timestamp >= start_date,
                EngagementEvent.event_type == 'view'
            )
        )
        
        interactions = await self.db_session.scalar(interaction_query)
        views = await self.db_session.scalar(view_query)
        
        return float(interactions) / float(views) if views > 0 else 0.0
    
    def _calculate_content_engagement_score(
        self,
        views: int,
        likes: int,
        shares: int,
        comments: int
    ) -> float:
        """Calculate weighted engagement score for content."""
        # Define weights for different engagement types
        weights = {
            'view': 1.0,
            'like': 3.0,
            'share': 5.0,
            'comment': 4.0
        }
        
        score = (
            views * weights['view'] +
            likes * weights['like'] +
            shares * weights['share'] +
            comments * weights['comment']
        )
        
        # Normalize by views to get average engagement per view
        return score / views if views > 0 else 0.0
    
    async def _calculate_engagement_score(
        self,
        events: List[EngagementEvent]
    ) -> float:
        """Calculate overall engagement score."""
        if not events:
            return 0.0
        
        # Weight different event types
        event_weights = {
            'view': 1.0,
            'click': 2.0,
            'like': 3.0,
            'comment': 4.0,
            'share': 5.0,
            'conversion': 10.0
        }
        
        total_score = 0.0
        for event in events:
            weight = event_weights.get(event.event_type, 1.0)
            total_score += weight
        
        # Calculate time-decayed score
        now = datetime.utcnow()
        time_weighted_score = 0.0
        
        for event in events:
            days_old = (now - event.timestamp).days
            time_decay = 1.0 / (1.0 + days_old * 0.1)  # 10% decay per day
            weight = event_weights.get(event.event_type, 1.0)
            time_weighted_score += weight * time_decay
        
        return time_weighted_score
    
    async def _calculate_retention_rate(
        self,
        events: List[EngagementEvent]
    ) -> float:
        """Calculate user retention rate."""
        if not events:
            return 0.0
        
        # Group events by date
        events_by_date = {}
        for event in events:
            date = event.timestamp.date()
            if date not in events_by_date:
                events_by_date[date] = []
            events_by_date[date].append(event)
        
        # Calculate consecutive days of engagement
        dates = sorted(events_by_date.keys())
        if len(dates) < 2:
            return 0.0
        
        consecutive_days = 0
        max_consecutive = 0
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                consecutive_days += 1
                max_consecutive = max(max_consecutive, consecutive_days)
            else:
                consecutive_days = 0
        
        # Calculate retention as ratio of active days to total period
        total_days = (dates[-1] - dates[0]).days + 1
        active_days = len(dates)
        
        return float(active_days) / float(total_days) if total_days > 0 else 0.0
    
    async def _get_top_engaged_users(
        self,
        start_date: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top engaged users."""
        query = select(
            EngagementEvent.user_id,
            func.count(EngagementEvent.id).label('event_count'),
            func.count(func.distinct(EngagementEvent.event_type)).label(
                'unique_event_types'
            )
        ).where(
            EngagementEvent.timestamp >= start_date
        ).group_by(
            EngagementEvent.user_id
        ).order_by(
            func.count(EngagementEvent.id).desc()
        ).limit(limit)
        
        result = await self.db_session.execute(query)
        
        top_users = []
        for row in result:
            top_users.append({
                'user_id': row.user_id,
                'event_count': row.event_count,
                'unique_event_types': row.unique_event_types
            })
        
        return top_users
    
    async def _fetch_user_events_in_range(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[EngagementEvent]:
        """Fetch events in a specific date range."""
        query = select(EngagementEvent).where(
            and_(
                EngagementEvent.user_id == user_id,
                EngagementEvent.timestamp >= start_date,
                EngagementEvent.timestamp < end_date
            )
        )
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    def _get_start_date(self, time_range: TimeRange) -> datetime:
        """Get start date based on time range."""
        now = datetime.utcnow()
        
        if time_range == TimeRange.DAILY:
            return now - timedelta(days=1)
        elif time_range == TimeRange.WEEKLY:
            return now - timedelta(weeks=1)
        elif time_range == TimeRange.MONTHLY:
            return now - timedelta(days=30)
        elif time_range == TimeRange.QUARTERLY:
            return now - timedelta(days=90)
        elif time_range == TimeRange.YEARLY:
            return now - timedelta(days=365)
        else:
            return now - timedelta(days=7)  # Default to weekly
    
    def _get_previous_time_range(self, time_range: TimeRange) -> TimeRange:
        """Get the previous time range for trend calculation."""
        # For simplicity, return the same time range
        # In practice, you might want different logic
        return time_range