from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    IterationPlan,
    IterationHistory,
    FeatureArchive,
    IterationStatus,
    ArchiveReason
)
from ..models.schemas import (
    IterationPlanCreate,
    IterationPlanUpdate,
    IterationHistoryCreate,
    FeatureArchiveCreate
)


class IterationPlanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: IterationPlanCreate) -> IterationPlan:
        """Create a new iteration plan."""
        plan = IterationPlan(
            feature_id=data.feature_id,
            priority_score=data.priority_score,
            iteration_number=data.iteration_number,
            planned_changes=data.planned_changes,
            target_metrics=data.target_metrics,
            scheduled_at=data.scheduled_at,
            status=IterationStatus.PENDING
        )
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def get_by_id(self, plan_id: int) -> Optional[IterationPlan]:
        stmt = select(IterationPlan).where(
            IterationPlan.id == plan_id
        ).options(selectinload(IterationPlan.history))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_feature_id(
        self, 
        feature_id: int,
        status: Optional[IterationStatus] = None
    ) -> List[IterationPlan]:
        stmt = select(IterationPlan).where(
            IterationPlan.feature_id == feature_id
        ).order_by(desc(IterationPlan.iteration_number))
        
        if status:
            stmt = stmt.where(IterationPlan.status == status)
            
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_by_priority(
        self,
        limit: int = 10,
        min_priority: Optional[float] = None
    ) -> List[IterationPlan]:
        """Get pending plans ordered by priority score."""
        stmt = select(IterationPlan).where(
            and_(
                IterationPlan.status == IterationStatus.PENDING,
                IterationPlan.scheduled_at <= datetime.utcnow()
            )
        ).order_by(desc(IterationPlan.priority_score))
        
        if min_priority:
            stmt = stmt.where(IterationPlan.priority_score >= min_priority)
            
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        plan_id: int,
        status: IterationStatus,
        completed_at: Optional[datetime] = None
    ) -> Optional[IterationPlan]:
        stmt = update(IterationPlan).where(
            IterationPlan.id == plan_id
        ).values(
            status=status,
            completed_at=completed_at or (datetime.utcnow() if status == IterationStatus.COMPLETED else None),
            updated_at=datetime.utcnow()
        ).returning(IterationPlan)
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def get_latest_iteration_number(self, feature_id: int) -> int:
        stmt = select(IterationPlan.iteration_number).where(
            IterationPlan.feature_id == feature_id
        ).order_by(desc(IterationPlan.iteration_number)).limit(1)
        
        result = await self.session.execute(stmt)
        latest = result.scalar_one_or_none()
        return latest or 0


class IterationHistoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: IterationHistoryCreate) -> IterationHistory:
        """Record iteration execution history."""
        history = IterationHistory(
            plan_id=data.plan_id,
            feature_id=data.feature_id,
            executed_at=data.executed_at or datetime.utcnow(),
            execution_duration=data.execution_duration,
            changes_applied=data.changes_applied,
            metrics_before=data.metrics_before,
            metrics_after=data.metrics_after,
            success=data.success,
            error_message=data.error_message
        )
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history

    async def get_by_feature_id(
        self,
        feature_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[IterationHistory]:
        stmt = select(IterationHistory).where(
            IterationHistory.feature_id == feature_id
        ).order_by(desc(IterationHistory.executed_at)).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_successful_count(self, feature_id: int) -> int:
        stmt = select(IterationHistory).where(
            and_(
                IterationHistory.feature_id == feature_id,
                IterationHistory.success == True
            )
        )
        result = await self.session.execute(stmt)
        return len(result.scalars().all())

    async def get_recent_performance(
        self,
        feature_id: int,
        days: int = 30
    ) -> List[IterationHistory]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stmt = select(IterationHistory).where(
            and_(
                IterationHistory.feature_id == feature_id,
                IterationHistory.executed_at >= cutoff_date
            )
        ).order_by(desc(IterationHistory.executed_at))
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class FeatureArchiveRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def archive_feature(
        self,
        data: FeatureArchiveCreate
    ) -> FeatureArchive:
        """Archive a low-performing feature."""
        archive = FeatureArchive(
            feature_id=data.feature_id,
            reason=data.reason,
            final_metrics=data.final_metrics,
            iteration_count=data.iteration_count,
            archived_at=datetime.utcnow(),
            archived_by=data.archived_by,
            notes=data.notes
        )
        self.session.add(archive)
        await self.session.commit()
        await self.session.refresh(archive)
        return archive

    async def get_archived_features(
        self,
        reason: Optional[ArchiveReason] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[FeatureArchive]:
        stmt = select(FeatureArchive).order_by(
            desc(FeatureArchive.archived_at)
        ).limit(limit).offset(offset)
        
        if reason:
            stmt = stmt.where(FeatureArchive.reason == reason)
            
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def is_archived(self, feature_id: int) -> bool:
        stmt = select(FeatureArchive.id).where(
            FeatureArchive.feature_id == feature_id
        ).limit(1)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def restore_feature(self, feature_id: int) -> bool:
        """Soft delete archive record to restore feature."""
        stmt = update(FeatureArchive).where(
            FeatureArchive.feature_id == feature_id
        ).values(
            restored_at=datetime.utcnow()
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0


class AutomatedIterationRepository:
    def __init__(self, session: AsyncSession):
        self.plan_repo = IterationPlanRepository(session)
        self.history_repo = IterationHistoryRepository(session)
        self.archive_repo = FeatureArchiveRepository(session)
        self.session = session

    async def get_features_for_iteration(
        self,
        min_priority_score: float = 0.3,
        max_features: int = 10
    ) -> List[dict]:
        """Get features eligible for automated iteration."""
        # Complex query to get features with their latest metrics
        # and filter by priority score
        stmt = select(
            IterationPlan.feature_id,
            IterationPlan.priority_score,
            IterationPlan.iteration_number
        ).where(
            and_(
                IterationPlan.status == IterationStatus.PENDING,
                IterationPlan.priority_score >= min_priority_score,
                IterationPlan.scheduled_at <= datetime.utcnow()
            )
        ).group_by(
            IterationPlan.feature_id,
            IterationPlan.priority_score,
            IterationPlan.iteration_number
        ).order_by(
            desc(IterationPlan.priority_score)
        ).limit(max_features)
        
        result = await self.session.execute(stmt)
        return [dict(row) for row in result]

    async def get_low_performing_features(
        self,
        performance_threshold: float = 0.2,
        min_iterations: int = 3,
        days_lookback: int = 30
    ) -> List[int]:
        """Identify features for automatic archival."""
        # Get features with poor performance metrics
        # after multiple iterations
        cutoff_date = datetime.utcnow() - timedelta(days=days_lookback)
        
        stmt = select(
            IterationHistory.feature_id
        ).where(
            IterationHistory.executed_at >= cutoff_date
        ).group_by(
            IterationHistory.feature_id
        ).having(
            and_(
                func.count(IterationHistory.id) >= min_iterations,
                func.avg(
                    func.json_extract_path_text(
                        IterationHistory.metrics_after,
                        'performance_score'
                    ).cast(Float)
                ) < performance_threshold
            )
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

from datetime import timedelta
from sqlalchemy import func, Float