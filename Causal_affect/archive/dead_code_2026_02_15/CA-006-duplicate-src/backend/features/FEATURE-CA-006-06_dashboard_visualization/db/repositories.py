from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.db import Base
from core.exceptions import NotFoundError
from features.FEATURE-CA-006-01_location_tracking.db.models import Location
from features.FEATURE-CA-006-02_shift_management.db.models import Shift, ShiftAssignment
from features.FEATURE-CA-006-03_task_management.db.models import Task, TaskStatus
from features.FEATURE-CA-006-04_communication_hub.db.models import Message, Announcement
from features.FEATURE-CA-006-05_reporting_analytics.db.models import Report, ReportMetric


class DashboardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_overview_stats(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get overview statistics for dashboard."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Active users count
        active_users_stmt = select(func.count(func.distinct(Location.user_id))).where(
            and_(
                Location.organization_id == organization_id,
                Location.timestamp >= start_date,
                Location.timestamp <= end_date
            )
        )
        active_users = await self.session.scalar(active_users_stmt)

        # Total shifts
        shifts_stmt = select(func.count(Shift.id)).where(
            and_(
                Shift.organization_id == organization_id,
                Shift.start_time >= start_date,
                Shift.end_time <= end_date
            )
        )
        total_shifts = await self.session.scalar(shifts_stmt)

        # Tasks stats
        tasks_stmt = select(
            func.count(Task.id),
            func.sum(func.cast(Task.status == TaskStatus.COMPLETED, int))
        ).where(
            and_(
                Task.organization_id == organization_id,
                Task.created_at >= start_date,
                Task.created_at <= end_date
            )
        )
        result = await self.session.execute(tasks_stmt)
        total_tasks, completed_tasks = result.first()

        # Messages count
        messages_stmt = select(func.count(Message.id)).where(
            and_(
                Message.organization_id == organization_id,
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        )
        total_messages = await self.session.scalar(messages_stmt)

        return {
            "active_users": active_users or 0,
            "total_shifts": total_shifts or 0,
            "total_tasks": total_tasks or 0,
            "completed_tasks": completed_tasks or 0,
            "task_completion_rate": (completed_tasks / total_tasks * 100) if total_tasks else 0,
            "total_messages": total_messages or 0,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }

    async def get_activity_timeline(
        self,
        organization_id: int,
        hours: int = 24,
        interval_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Get activity timeline data for charts."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        intervals = []
        current = start_time
        
        while current <= end_time:
            next_interval = current + timedelta(minutes=interval_minutes)
            
            # Count activities in this interval
            location_count = await self.session.scalar(
                select(func.count(Location.id)).where(
                    and_(
                        Location.organization_id == organization_id,
                        Location.timestamp >= current,
                        Location.timestamp < next_interval
                    )
                )
            )
            
            task_count = await self.session.scalar(
                select(func.count(Task.id)).where(
                    and_(
                        Task.organization_id == organization_id,
                        or_(
                            and_(Task.created_at >= current, Task.created_at < next_interval),
                            and_(Task.updated_at >= current, Task.updated_at < next_interval)
                        )
                    )
                )
            )
            
            message_count = await self.session.scalar(
                select(func.count(Message.id)).where(
                    and_(
                        Message.organization_id == organization_id,
                        Message.created_at >= current,
                        Message.created_at < next_interval
                    )
                )
            )
            
            intervals.append({
                "timestamp": current.isoformat(),
                "locations": location_count or 0,
                "tasks": task_count or 0,
                "messages": message_count or 0
            })
            
            current = next_interval
        
        return intervals

    async def get_task_distribution(
        self,
        organization_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get task distribution by status."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(
            Task.status,
            func.count(Task.id)
        ).where(
            and_(
                Task.organization_id == organization_id,
                Task.created_at >= start_date
            )
        ).group_by(Task.status)
        
        result = await self.session.execute(stmt)
        
        return [
            {
                "status": status.value,
                "count": count,
                "percentage": 0  # Will be calculated on frontend
            }
            for status, count in result
        ]

    async def get_shift_coverage(
        self,
        organization_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get shift coverage data."""
        start_date = datetime.utcnow().date()
        coverage_data = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            next_date = current_date + timedelta(days=1)
            
            # Count shifts for the day
            shifts_stmt = select(func.count(Shift.id)).where(
                and_(
                    Shift.organization_id == organization_id,
                    Shift.start_time >= current_date,
                    Shift.start_time < next_date
                )
            )
            total_shifts = await self.session.scalar(shifts_stmt)
            
            # Count assigned shifts
            assigned_stmt = select(func.count(func.distinct(ShiftAssignment.shift_id))).join(
                Shift, ShiftAssignment.shift_id == Shift.id
            ).where(
                and_(
                    Shift.organization_id == organization_id,
                    Shift.start_time >= current_date,
                    Shift.start_time < next_date
                )
            )
            assigned_shifts = await self.session.scalar(assigned_stmt)
            
            coverage_data.append({
                "date": current_date.isoformat(),
                "total_shifts": total_shifts or 0,
                "assigned_shifts": assigned_shifts or 0,
                "coverage_rate": (assigned_shifts / total_shifts * 100) if total_shifts else 0
            })
        
        return coverage_data

    async def get_recent_activities(
        self,
        organization_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent activities across all features."""
        activities = []
        
        # Recent tasks
        tasks_stmt = select(Task).where(
            Task.organization_id == organization_id
        ).order_by(desc(Task.created_at)).limit(limit // 4)
        
        tasks = await self.session.execute(tasks_stmt)
        for task in tasks.scalars():
            activities.append({
                "type": "task",
                "title": task.title,
                "status": task.status.value,
                "timestamp": task.created_at.isoformat(),
                "user_id": task.assigned_to
            })
        
        # Recent messages
        messages_stmt = select(Message).where(
            Message.organization_id == organization_id
        ).order_by(desc(Message.created_at)).limit(limit // 4)
        
        messages = await self.session.execute(messages_stmt)
        for message in messages.scalars():
            activities.append({
                "type": "message",
                "content": message.content[:100] + "..." if len(message.content) > 100 else message.content,
                "timestamp": message.created_at.isoformat(),
                "user_id": message.sender_id
            })
        
        # Recent announcements
        announcements_stmt = select(Announcement).where(
            Announcement.organization_id == organization_id
        ).order_by(desc(Announcement.created_at)).limit(limit // 4)
        
        announcements = await self.session.execute(announcements_stmt)
        for announcement in announcements.scalars():
            activities.append({
                "type": "announcement",
                "title": announcement.title,
                "priority": announcement.priority.value,
                "timestamp": announcement.created_at.isoformat(),
                "user_id": announcement.created_by
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return activities[:limit]

    async def get_performance_metrics(
        self,
        organization_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get performance metrics from reports."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get latest report metrics
        metrics_stmt = select(ReportMetric).join(
            Report, ReportMetric.report_id == Report.id
        ).where(
            and_(
                Report.organization_id == organization_id,
                Report.created_at >= start_date
            )
        ).order_by(desc(Report.created_at))
        
        result = await self.session.execute(metrics_stmt)
        metrics = result.scalars().all()
        
        # Group metrics by name
        metric_data = {}
        for metric in metrics:
            if metric.metric_name not in metric_data:
                metric_data[metric.metric_name] = []
            metric_data[metric.metric_name].append({
                "value": metric.value,
                "timestamp": metric.created_at.isoformat()
            })
        
        return metric_data

    async def get_location_heatmap(
        self,
        organization_id: int,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get location data for heatmap visualization."""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        stmt = select(
            Location.latitude,
            Location.longitude,
            func.count(Location.id).label("intensity")
        ).where(
            and_(
                Location.organization_id == organization_id,
                Location.timestamp >= start_time
            )
        ).group_by(
            func.round(Location.latitude, 4),
            func.round(Location.longitude, 4)
        )
        
        result = await self.session.execute(stmt)
        
        return [
            {
                "lat": float(row.latitude),
                "lng": float(row.longitude),
                "intensity": row.intensity
            }
            for row in result
        ]

    async def get_user_activity_summary(
        self,
        organization_id: int,
        user_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get activity summary for a specific user."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Tasks assigned
        tasks_count = await self.session.scalar(
            select(func.count(Task.id)).where(
                and_(
                    Task.organization_id == organization_id,
                    Task.assigned_to == user_id,
                    Task.created_at >= start_date
                )
            )
        )
        
        # Tasks completed
        completed_count = await self.session.scalar(
            select(func.count(Task.id)).where(
                and_(
                    Task.organization_id == organization_id,
                    Task.assigned_to == user_id,
                    Task.status == TaskStatus.COMPLETED,
                    Task.updated_at >= start_date
                )
            )
        )
        
        # Messages sent
        messages_count = await self.session.scalar(
            select(func.count(Message.id)).where(
                and_(
                    Message.organization_id == organization_id,
                    Message.sender_id == user_id,
                    Message.created_at >= start_date
                )
            )
        )
        
        # Shifts assigned
        shifts_count = await self.session.scalar(
            select(func.count(ShiftAssignment.id)).join(
                Shift, ShiftAssignment.shift_id == Shift.id
            ).where(
                and_(
                    Shift.organization_id == organization_id,
                    ShiftAssignment.user_id == user_id,
                    Shift.start_time >= start_date
                )
            )
        )
        
        return {
            "user_id": user_id,
            "period_days": days,
            "tasks_assigned": tasks_count or 0,
            "tasks_completed": completed_count or 0,
            "completion_rate": (completed_count / tasks_count * 100) if tasks_count else 0,
            "messages_sent": messages_count or 0,
            "shifts_assigned": shifts_count or 0
        }
