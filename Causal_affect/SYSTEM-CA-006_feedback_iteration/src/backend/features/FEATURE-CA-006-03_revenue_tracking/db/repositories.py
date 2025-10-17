from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from uuid import UUID
import asyncio

from sqlalchemy import select, func, and_, or_, desc, asc, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import text

from features.FEATURE-CA-006-01_visitor_analytics.db.models import Visitor, Session, PageView
from features.FEATURE-CA-006-03_revenue_tracking.db.models import (
    ConversionEvent,
    ConversionGoal,
    AttributionModel,
    RevenueMetric,
    FunnelStep,
    FunnelAnalysis
)
from features.FEATURE-CA-006-03_revenue_tracking.models.schemas import (
    ConversionEventCreate,
    ConversionGoalCreate,
    AttributionModelCreate,
    RevenueMetricCreate,
    FunnelStepCreate,
    ConversionFilter,
    RevenueFilter,
    FunnelFilter,
    AttributionType,
    ConversionStatus,
    TimeGranularity
)
from core.exceptions import NotFoundError, ValidationError


class ConversionRepository:
    """Repository for conversion event operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_event(self, data: ConversionEventCreate) -> ConversionEvent:
        """Create a new conversion event."""
        event = ConversionEvent(**data.model_dump())
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event
    
    async def get_event(self, event_id: UUID) -> ConversionEvent:
        """Get a conversion event by ID."""
        query = select(ConversionEvent).where(
            ConversionEvent.id == event_id
        ).options(
            selectinload(ConversionEvent.goal),
            selectinload(ConversionEvent.visitor),
            selectinload(ConversionEvent.session)
        )
        
        result = await self.session.execute(query)
        event = result.scalar_one_or_none()
        
        if not event:
            raise NotFoundError(f"Conversion event {event_id} not found")
        
        return event
    
    async def list_events(
        self,
        filter_params: ConversionFilter,
        offset: int = 0,
        limit: int = 100
    ) -> Tuple[List[ConversionEvent], int]:
        """List conversion events with filtering."""
        query = select(ConversionEvent).options(
            selectinload(ConversionEvent.goal),
            selectinload(ConversionEvent.visitor)
        )
        
        # Apply filters
        conditions = []
        
        if filter_params.goal_id:
            conditions.append(ConversionEvent.goal_id == filter_params.goal_id)
        
        if filter_params.visitor_id:
            conditions.append(ConversionEvent.visitor_id == filter_params.visitor_id)
        
        if filter_params.status:
            conditions.append(ConversionEvent.status == filter_params.status)
        
        if filter_params.start_date:
            conditions.append(ConversionEvent.created_at >= filter_params.start_date)
        
        if filter_params.end_date:
            conditions.append(ConversionEvent.created_at <= filter_params.end_date)
        
        if filter_params.min_value is not None:
            conditions.append(ConversionEvent.value >= filter_params.min_value)
        
        if filter_params.max_value is not None:
            conditions.append(ConversionEvent.value <= filter_params.max_value)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        query = query.order_by(desc(ConversionEvent.created_at))
        
        result = await self.session.execute(query)
        events = result.scalars().all()
        
        return events, total
    
    async def calculate_attribution(
        self,
        event_id: UUID,
        model_type: AttributionType,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate attribution for a conversion event."""
        event = await self.get_event(event_id)
        
        # Get all touchpoints in lookback window
        touchpoint_query = select(PageView).join(Session).where(
            and_(
                Session.visitor_id == event.visitor_id,
                PageView.created_at >= event.created_at - timedelta(days=lookback_days),
                PageView.created_at <= event.created_at
            )
        ).order_by(PageView.created_at)
        
        result = await self.session.execute(touchpoint_query)
        touchpoints = result.scalars().all()
        
        if not touchpoints:
            return {"touchpoints": [], "attribution": {}}
        
        # Calculate attribution based on model
        attribution = self._calculate_attribution_weights(
            touchpoints, model_type, event.value
        )
        
        return {
            "touchpoints": len(touchpoints),
            "attribution": attribution,
            "model_type": model_type,
            "lookback_days": lookback_days
        }
    
    def _calculate_attribution_weights(
        self,
        touchpoints: List[PageView],
        model_type: AttributionType,
        conversion_value: Decimal
    ) -> Dict[str, Decimal]:
        """Calculate attribution weights for touchpoints."""
        attribution = {}
        
        if model_type == AttributionType.LAST_CLICK:
            last = touchpoints[-1]
            attribution[last.source or "direct"] = conversion_value
        
        elif model_type == AttributionType.FIRST_CLICK:
            first = touchpoints[0]
            attribution[first.source or "direct"] = conversion_value
        
        elif model_type == AttributionType.LINEAR:
            weight = conversion_value / len(touchpoints)
            for tp in touchpoints:
                source = tp.source or "direct"
                attribution[source] = attribution.get(source, Decimal(0)) + weight
        
        elif model_type == AttributionType.TIME_DECAY:
            # More recent touchpoints get higher weight
            total_weight = sum(i + 1 for i in range(len(touchpoints)))
            for i, tp in enumerate(touchpoints):
                weight = (i + 1) / total_weight * conversion_value
                source = tp.source or "direct"
                attribution[source] = attribution.get(source, Decimal(0)) + weight
        
        elif model_type == AttributionType.POSITION_BASED:
            # 40% first, 40% last, 20% middle
            if len(touchpoints) == 1:
                source = touchpoints[0].source or "direct"
                attribution[source] = conversion_value
            elif len(touchpoints) == 2:
                for tp, weight in zip(touchpoints, [0.5, 0.5]):
                    source = tp.source or "direct"
                    attribution[source] = attribution.get(source, Decimal(0)) + conversion_value * Decimal(str(weight))
            else:
                # First touch: 40%
                source = touchpoints[0].source or "direct"
                attribution[source] = conversion_value * Decimal("0.4")
                
                # Last touch: 40%
                source = touchpoints[-1].source or "direct"
                attribution[source] = attribution.get(source, Decimal(0)) + conversion_value * Decimal("0.4")
                
                # Middle touches: 20% split
                middle_weight = Decimal("0.2") / (len(touchpoints) - 2)
                for tp in touchpoints[1:-1]:
                    source = tp.source or "direct"
                    attribution[source] = attribution.get(source, Decimal(0)) + conversion_value * middle_weight
        
        return attribution


class RevenueRepository:
    """Repository for revenue metric operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_metric(self, data: RevenueMetricCreate) -> RevenueMetric:
        """Create a new revenue metric."""
        metric = RevenueMetric(**data.model_dump())
        self.session.add(metric)
        await self.session.commit()
        await self.session.refresh(metric)
        return metric
    
    async def calculate_ltv(
        self,
        visitor_id: UUID,
        days: int = 365
    ) -> Dict[str, Any]:
        """Calculate lifetime value for a visitor."""
        # Get all conversions for visitor
        query = select(
            func.sum(ConversionEvent.value).label("total_revenue"),
            func.count(ConversionEvent.id).label("conversion_count"),
            func.min(ConversionEvent.created_at).label("first_conversion"),
            func.max(ConversionEvent.created_at).label("last_conversion")
        ).where(
            and_(
                ConversionEvent.visitor_id == visitor_id,
                ConversionEvent.status == ConversionStatus.COMPLETED,
                ConversionEvent.created_at >= datetime.utcnow() - timedelta(days=days)
            )
        )
        
        result = await self.session.execute(query)
        data = result.one()
        
        if not data.conversion_count:
            return {
                "ltv": Decimal(0),
                "total_revenue": Decimal(0),
                "conversion_count": 0,
                "average_order_value": Decimal(0),
                "days_active": 0
            }
        
        days_active = (data.last_conversion - data.first_conversion).days + 1
        
        return {
            "ltv": data.total_revenue,
            "total_revenue": data.total_revenue,
            "conversion_count": data.conversion_count,
            "average_order_value": data.total_revenue / data.conversion_count,
            "days_active": days_active,
            "first_conversion": data.first_conversion,
            "last_conversion": data.last_conversion
        }
    
    async def get_revenue_metrics(
        self,
        filter_params: RevenueFilter,
        granularity: TimeGranularity = TimeGranularity.DAILY
    ) -> List[Dict[str, Any]]:
        """Get revenue metrics with time series data."""
        # Build time truncation based on granularity
        if granularity == TimeGranularity.HOURLY:
            time_trunc = func.date_trunc("hour", ConversionEvent.created_at)
        elif granularity == TimeGranularity.DAILY:
            time_trunc = func.date_trunc("day", ConversionEvent.created_at)
        elif granularity == TimeGranularity.WEEKLY:
            time_trunc = func.date_trunc("week", ConversionEvent.created_at)
        elif granularity == TimeGranularity.MONTHLY:
            time_trunc = func.date_trunc("month", ConversionEvent.created_at)
        
        query = select(
            time_trunc.label("period"),
            func.sum(ConversionEvent.value).label("revenue"),
            func.count(ConversionEvent.id).label("conversions"),
            func.avg(ConversionEvent.value).label("avg_value"),
            func.count(func.distinct(ConversionEvent.visitor_id)).label("unique_customers")
        ).where(
            ConversionEvent.status == ConversionStatus.COMPLETED
        )
        
        # Apply filters
        conditions = []
        
        if filter_params.start_date:
            conditions.append(ConversionEvent.created_at >= filter_params.start_date)
        
        if filter_params.end_date:
            conditions.append(ConversionEvent.created_at <= filter_params.end_date)
        
        if filter_params.goal_ids:
            conditions.append(ConversionEvent.goal_id.in_(filter_params.goal_ids))
        
        if filter_params.source:
            conditions.append(ConversionEvent.source == filter_params.source)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.group_by(time_trunc).order_by(time_trunc)
        
        result = await self.session.execute(query)
        metrics = []
        
        for row in result:
            metrics.append({
                "period": row.period,
                "revenue": row.revenue or Decimal(0),
                "conversions": row.conversions,
                "avg_value": row.avg_value or Decimal(0),
                "unique_customers": row.unique_customers,
                "revenue_per_customer": (
                    row.revenue / row.unique_customers if row.unique_customers > 0
                    else Decimal(0)
                )
            })
        
        return metrics
    
    async def calculate_cohort_ltv(
        self,
        cohort_date: datetime,
        days_range: int = 90
    ) -> Dict[str, Any]:
        """Calculate LTV for a cohort of users."""
        cohort_end = cohort_date + timedelta(days=1)
        
        # Get visitors from cohort
        visitor_query = select(Visitor.id).where(
            and_(
                Visitor.created_at >= cohort_date,
                Visitor.created_at < cohort_end
            )
        )
        
        visitor_result = await self.session.execute(visitor_query)
        visitor_ids = [row[0] for row in visitor_result]
        
        if not visitor_ids:
            return {"cohort_size": 0, "metrics": []}
        
        # Calculate revenue by days since first visit
        metrics = []
        
        for day in range(0, days_range + 1):
            day_start = cohort_date + timedelta(days=day)
            day_end = day_start + timedelta(days=1)
            
            revenue_query = select(
                func.sum(ConversionEvent.value).label("revenue"),
                func.count(func.distinct(ConversionEvent.visitor_id)).label("customers")
            ).where(
                and_(
                    ConversionEvent.visitor_id.in_(visitor_ids),
                    ConversionEvent.created_at >= cohort_date,
                    ConversionEvent.created_at < day_end,
                    ConversionEvent.status == ConversionStatus.COMPLETED
                )
            )
            
            result = await self.session.execute(revenue_query)
            data = result.one()
            
            metrics.append({
                "day": day,
                "cumulative_revenue": data.revenue or Decimal(0),
                "cumulative_customers": data.customers,
                "ltv_per_visitor": (
                    data.revenue / len(visitor_ids) if data.revenue else Decimal(0)
                )
            })
        
        return {
            "cohort_date": cohort_date,
            "cohort_size": len(visitor_ids),
            "metrics": metrics
        }


class FunnelRepository:
    """Repository for funnel analysis operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_funnel(
        self,
        name: str,
        steps: List[FunnelStepCreate]
    ) -> FunnelAnalysis:
        """Create a new funnel with steps."""
        funnel = FunnelAnalysis(name=name)
        self.session.add(funnel)
        await self.session.flush()
        
        for order, step_data in enumerate(steps, 1):
            step = FunnelStep(
                funnel_id=funnel.id,
                step_order=order,
                **step_data.model_dump()
            )
            self.session.add(step)
        
        await self.session.commit()
        await self.session.refresh(funnel)
        return funnel
    
    async def analyze_funnel(
        self,
        funnel_id: UUID,
        filter_params: FunnelFilter
    ) -> Dict[str, Any]:
        """Analyze funnel conversion rates."""
        # Get funnel with steps
        funnel_query = select(FunnelAnalysis).where(
            FunnelAnalysis.id == funnel_id
        ).options(selectinload(FunnelAnalysis.steps))
        
        result = await self.session.execute(funnel_query)
        funnel = result.scalar_one_or_none()
        
        if not funnel:
            raise NotFoundError(f"Funnel {funnel_id} not found")
        
        # Sort steps by order
        steps = sorted(funnel.steps, key=lambda s: s.step_order)
        
        # Analyze each step
        analysis = {
            "funnel_id": funnel_id,
            "funnel_name": funnel.name,
            "steps": [],
            "overall_conversion": Decimal(0),
            "total_visitors": 0
        }
        
        previous_visitors = None
        
        for step in steps:
            step_visitors = await self._get_step_visitors(
                step, filter_params, previous_visitors
            )
            
            step_count = len(step_visitors)
            
            step_data = {
                "step_order": step.step_order,
                "step_name": step.name,
                "visitors": step_count,
                "conversion_rate": Decimal(0),
                "drop_off_rate": Decimal(0)
            }
            
            if step.step_order == 1:
                analysis["total_visitors"] = step_count
            
            if analysis["total_visitors"] > 0:
                step_data["conversion_rate"] = (
                    Decimal(step_count) / Decimal(analysis["total_visitors"]) * 100
                )
            
            if previous_visitors is not None and len(previous_visitors) > 0:
                step_data["drop_off_rate"] = (
                    Decimal(len(previous_visitors) - step_count) /
                    Decimal(len(previous_visitors)) * 100
                )
            
            analysis["steps"].append(step_data)
            previous_visitors = step_visitors
        
        # Calculate overall conversion
        if analysis["total_visitors"] > 0 and steps:
            last_step = analysis["steps"][-1]
            analysis["overall_conversion"] = last_step["conversion_rate"]
        
        return analysis
    
    async def _get_step_visitors(
        self,
        step: FunnelStep,
        filter_params: FunnelFilter,
        previous_visitors: Optional[set] = None
    ) -> set:
        """Get visitors who completed a funnel step."""
        if step.event_type == "page_view":
            query = select(PageView.visitor_id).join(Session).where(
                PageView.path == step.event_value
            )
        elif step.event_type == "conversion":
            query = select(ConversionEvent.visitor_id).join(ConversionGoal).where(
                ConversionGoal.name == step.event_value
            )
        else:
            return set()
        
        # Apply time filters
        if filter_params.start_date:
            if step.event_type == "page_view":
                query = query.where(PageView.created_at >= filter_params.start_date)
            else:
                query = query.where(ConversionEvent.created_at >= filter_params.start_date)
        
        if filter_params.end_date:
            if step.event_type == "page_view":
                query = query.where(PageView.created_at <= filter_params.end_date)
            else:
                query = query.where(ConversionEvent.created_at <= filter_params.end_date)
        
        # Apply visitor filter from previous step
        if previous_visitors is not None:
            if step.event_type == "page_view":
                query = query.where(PageView.visitor_id.in_(previous_visitors))
            else:
                query = query.where(ConversionEvent.visitor_id.in_(previous_visitors))
        
        result = await self.session.execute(query.distinct())
        return {row[0] for row in result}
    
    async def get_funnel_comparison(
        self,
        funnel_ids: List[UUID],
        filter_params: FunnelFilter
    ) -> List[Dict[str, Any]]:
        """Compare multiple funnels performance."""
        comparisons = []
        
        for funnel_id in funnel_ids:
            analysis = await self.analyze_funnel(funnel_id, filter_params)
            comparisons.append(analysis)
        
        return comparisons


class GoalRepository:
    """Repository for conversion goal operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_goal(self, data: ConversionGoalCreate) -> ConversionGoal:
        """Create a new conversion goal."""
        goal = ConversionGoal(**data.model_dump())
        self.session.add(goal)
        await self.session.commit()
        await self.session.refresh(goal)
        return goal
    
    async def get_goal(self, goal_id: UUID) -> ConversionGoal:
        """Get a conversion goal by ID."""
        query = select(ConversionGoal).where(ConversionGoal.id == goal_id)
        result = await self.session.execute(query)
        goal = result.scalar_one_or_none()
        
        if not goal:
            raise NotFoundError(f"Goal {goal_id} not found")
        
        return goal
    
    async def list_goals(
        self,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 100
    ) -> Tuple[List[ConversionGoal], int]:
        """List conversion goals."""
        query = select(ConversionGoal)
        
        if is_active is not None:
            query = query.where(ConversionGoal.is_active == is_active)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        query = query.order_by(ConversionGoal.created_at.desc())
        
        result = await self.session.execute(query)
        goals = result.scalars().all()
        
        return goals, total
    
    async def get_goal_performance(
        self,
        goal_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get performance metrics for a goal."""
        goal = await self.get_goal(goal_id)
        
        # Get conversion metrics
        metrics_query = select(
            func.count(ConversionEvent.id).label("total_conversions"),
            func.sum(ConversionEvent.value).label("total_revenue"),
            func.avg(ConversionEvent.value).label("avg_value"),
            func.count(func.distinct(ConversionEvent.visitor_id)).label("unique_converters")
        ).where(
            and_(
                ConversionEvent.goal_id == goal_id,
                ConversionEvent.created_at >= start_date,
                ConversionEvent.created_at <= end_date,
                ConversionEvent.status == ConversionStatus.COMPLETED
            )
        )
        
        result = await self.session.execute(metrics_query)
        metrics = result.one()
        
        # Get total visitors in period
        visitor_query = select(func.count(func.distinct(Visitor.id))).where(
            and_(
                Visitor.created_at >= start_date,
                Visitor.created_at <= end_date
            )
        )
        
        visitor_result = await self.session.execute(visitor_query)
        total_visitors = visitor_result.scalar_one()
        
        conversion_rate = Decimal(0)
        if total_visitors > 0:
            conversion_rate = (
                Decimal(metrics.unique_converters) / Decimal(total_visitors) * 100
            )
        
        return {
            "goal_id": goal_id,
            "goal_name": goal.name,
            "period": {
                "start": start_date,
                "end": end_date
            },
            "metrics": {
                "total_conversions": metrics.total_conversions,
                "unique_converters": metrics.unique_converters,
                "total_revenue": metrics.total_revenue or Decimal(0),
                "avg_value": metrics.avg_value or Decimal(0),
                "conversion_rate": conversion_rate,
                "total_visitors": total_visitors
            }
        }
