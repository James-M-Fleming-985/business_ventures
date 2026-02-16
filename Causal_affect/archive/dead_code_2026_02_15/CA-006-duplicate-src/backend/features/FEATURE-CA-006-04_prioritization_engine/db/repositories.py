from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.schemas import (
    FeatureCreate,
    FeatureUpdate,
    Feature,
    FeaturePriority,
    PriorityScore,
    EngagementMetrics,
    RevenueMetrics
)
from .models import FeatureModel, FeatureMetricsModel, PriorityHistoryModel
from ..exceptions import FeatureNotFoundError, DuplicateFeatureError


class FeatureRepository:
    """Repository for feature CRUD operations."""
    
    async def create(self, db: AsyncSession, feature: FeatureCreate) -> Feature:
        # Check for duplicates
        stmt = select(FeatureModel).where(FeatureModel.name == feature.name)
        existing = await db.execute(stmt)
        if existing.scalar_one_or_none():
            raise DuplicateFeatureError(f"Feature '{feature.name}' already exists")
        
        db_feature = FeatureModel(**feature.model_dump())
        db.add(db_feature)
        await db.commit()
        await db.refresh(db_feature)
        
        return Feature.model_validate(db_feature)
    
    async def get(self, db: AsyncSession, feature_id: int) -> Optional[Feature]:
        stmt = select(FeatureModel).where(FeatureModel.id == feature_id)
        result = await db.execute(stmt)
        db_feature = result.scalar_one_or_none()
        
        if not db_feature:
            raise FeatureNotFoundError(f"Feature {feature_id} not found")
        
        return Feature.model_validate(db_feature)
    
    async def list(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Feature]:
        stmt = select(FeatureModel)
        
        if status:
            stmt = stmt.where(FeatureModel.status == status)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        
        return [Feature.model_validate(f) for f in result.scalars().all()]
    
    async def update(
        self,
        db: AsyncSession,
        feature_id: int,
        feature_update: FeatureUpdate
    ) -> Feature:
        stmt = (
            update(FeatureModel)
            .where(FeatureModel.id == feature_id)
            .values(**feature_update.model_dump(exclude_unset=True))
            .returning(FeatureModel)
        )
        result = await db.execute(stmt)
        db_feature = result.scalar_one_or_none()
        
        if not db_feature:
            raise FeatureNotFoundError(f"Feature {feature_id} not found")
        
        await db.commit()
        await db.refresh(db_feature)
        
        return Feature.model_validate(db_feature)
    
    async def delete(self, db: AsyncSession, feature_id: int) -> bool:
        stmt = delete(FeatureModel).where(FeatureModel.id == feature_id)
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount > 0


class MetricsRepository:
    """Repository for feature metrics operations."""
    
    async def update_engagement(
        self,
        db: AsyncSession,
        feature_id: int,
        metrics: EngagementMetrics
    ) -> None:
        stmt = select(FeatureMetricsModel).where(
            FeatureMetricsModel.feature_id == feature_id
        )
        result = await db.execute(stmt)
        db_metrics = result.scalar_one_or_none()
        
        if db_metrics:
            stmt = (
                update(FeatureMetricsModel)
                .where(FeatureMetricsModel.feature_id == feature_id)
                .values(
                    views=metrics.views,
                    clicks=metrics.clicks,
                    conversion_rate=metrics.conversion_rate,
                    user_satisfaction=metrics.user_satisfaction,
                    updated_at=datetime.utcnow()
                )
            )
            await db.execute(stmt)
        else:
            db_metrics = FeatureMetricsModel(
                feature_id=feature_id,
                views=metrics.views,
                clicks=metrics.clicks,
                conversion_rate=metrics.conversion_rate,
                user_satisfaction=metrics.user_satisfaction
            )
            db.add(db_metrics)
        
        await db.commit()
    
    async def update_revenue(
        self,
        db: AsyncSession,
        feature_id: int,
        metrics: RevenueMetrics
    ) -> None:
        stmt = select(FeatureMetricsModel).where(
            FeatureMetricsModel.feature_id == feature_id
        )
        result = await db.execute(stmt)
        db_metrics = result.scalar_one_or_none()
        
        if db_metrics:
            stmt = (
                update(FeatureMetricsModel)
                .where(FeatureMetricsModel.feature_id == feature_id)
                .values(
                    revenue_impact=metrics.revenue_impact,
                    cost_reduction=metrics.cost_reduction,
                    roi=metrics.roi,
                    updated_at=datetime.utcnow()
                )
            )
            await db.execute(stmt)
        else:
            db_metrics = FeatureMetricsModel(
                feature_id=feature_id,
                revenue_impact=metrics.revenue_impact,
                cost_reduction=metrics.cost_reduction,
                roi=metrics.roi
            )
            db.add(db_metrics)
        
        await db.commit()
    
    async def get_metrics(
        self,
        db: AsyncSession,
        feature_id: int
    ) -> Optional[Dict[str, Any]]:
        stmt = select(FeatureMetricsModel).where(
            FeatureMetricsModel.feature_id == feature_id
        )
        result = await db.execute(stmt)
        db_metrics = result.scalar_one_or_none()
        
        if not db_metrics:
            return None
        
        return {
            "engagement": EngagementMetrics(
                views=db_metrics.views or 0,
                clicks=db_metrics.clicks or 0,
                conversion_rate=db_metrics.conversion_rate or 0.0,
                user_satisfaction=db_metrics.user_satisfaction or 0.0
            ),
            "revenue": RevenueMetrics(
                revenue_impact=db_metrics.revenue_impact or 0.0,
                cost_reduction=db_metrics.cost_reduction or 0.0,
                roi=db_metrics.roi or 0.0
            )
        }


class PriorityRepository:
    """Repository for feature priority operations."""
    
    async def calculate_priority_score(
        self,
        db: AsyncSession,
        feature_id: int
    ) -> PriorityScore:
        # Get feature with metrics
        stmt = (
            select(FeatureModel)
            .options(selectinload(FeatureModel.metrics))
            .where(FeatureModel.id == feature_id)
        )
        result = await db.execute(stmt)
        feature = result.scalar_one_or_none()
        
        if not feature:
            raise FeatureNotFoundError(f"Feature {feature_id} not found")
        
        metrics = feature.metrics
        if not metrics:
            return PriorityScore(
                feature_id=feature_id,
                total_score=0.0,
                engagement_score=0.0,
                revenue_score=0.0,
                calculated_at=datetime.utcnow()
            )
        
        # Calculate engagement score (40% weight)
        engagement_score = (
            (metrics.views or 0) * 0.1 +
            (metrics.clicks or 0) * 0.2 +
            (metrics.conversion_rate or 0) * 50 +
            (metrics.user_satisfaction or 0) * 10
        ) * 0.4
        
        # Calculate revenue score (60% weight)
        revenue_score = (
            (metrics.revenue_impact or 0) * 0.4 +
            (metrics.cost_reduction or 0) * 0.3 +
            (metrics.roi or 0) * 0.3
        ) * 0.6
        
        total_score = engagement_score + revenue_score
        
        # Update feature priority
        stmt = (
            update(FeatureModel)
            .where(FeatureModel.id == feature_id)
            .values(priority_score=total_score)
        )
        await db.execute(stmt)
        
        # Save to history
        history = PriorityHistoryModel(
            feature_id=feature_id,
            score=total_score,
            engagement_score=engagement_score,
            revenue_score=revenue_score
        )
        db.add(history)
        await db.commit()
        
        return PriorityScore(
            feature_id=feature_id,
            total_score=total_score,
            engagement_score=engagement_score,
            revenue_score=revenue_score,
            calculated_at=datetime.utcnow()
        )
    
    async def get_top_features(
        self,
        db: AsyncSession,
        limit: int = 5,
        status: Optional[str] = None
    ) -> List[FeaturePriority]:
        stmt = (
            select(FeatureModel)
            .options(selectinload(FeatureModel.metrics))
        )
        
        if status:
            stmt = stmt.where(FeatureModel.status == status)
        
        stmt = stmt.order_by(desc(FeatureModel.priority_score)).limit(limit)
        
        result = await db.execute(stmt)
        features = result.scalars().all()
        
        priorities = []
        for idx, feature in enumerate(features):
            priority = FeaturePriority(
                feature=Feature.model_validate(feature),
                priority_score=feature.priority_score or 0.0,
                rank=idx + 1,
                last_calculated=feature.metrics.updated_at if feature.metrics else None
            )
            priorities.append(priority)
        
        return priorities
    
    async def update_all_priorities(self, db: AsyncSession) -> None:
        """Recalculate priorities for all active features."""
        stmt = select(FeatureModel).where(
            or_(
                FeatureModel.status == "active",
                FeatureModel.status == "pending"
            )
        )
        result = await db.execute(stmt)
        features = result.scalars().all()
        
        for feature in features:
            await self.calculate_priority_score(db, feature.id)
    
    async def get_priority_history(
        self,
        db: AsyncSession,
        feature_id: int,
        days: int = 7
    ) -> List[PriorityScore]:
        since = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(PriorityHistoryModel)
            .where(
                and_(
                    PriorityHistoryModel.feature_id == feature_id,
                    PriorityHistoryModel.created_at >= since
                )
            )
            .order_by(PriorityHistoryModel.created_at)
        )
        result = await db.execute(stmt)
        history = result.scalars().all()
        
        return [
            PriorityScore(
                feature_id=h.feature_id,
                total_score=h.score,
                engagement_score=h.engagement_score,
                revenue_score=h.revenue_score,
                calculated_at=h.created_at
            )
            for h in history
        ]


# Repository instances
feature_repository = FeatureRepository()
metrics_repository = MetricsRepository()
priority_repository = PriorityRepository()