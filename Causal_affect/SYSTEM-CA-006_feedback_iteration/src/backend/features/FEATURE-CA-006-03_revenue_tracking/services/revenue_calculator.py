from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from enum import Enum
import asyncio

from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
import json

from ..db.models import RevenueEvent, Conversion
from ..db.repositories import RevenueEventRepository, ConversionRepository
from ..models.schemas import (
    RevenueMetrics,
    RevenueBreakdown,
    RevenueForecast,
    RevenueReport,
    RevenueEventCreate
)
from core.exceptions import BusinessLogicError, ValidationError
from core.cache import CacheManager


class RevenueEventType(str, Enum):
    CONVERSION = "conversion"
    REFUND = "refund"
    CHARGEBACK = "chargeback"
    ADJUSTMENT = "adjustment"
    COMMISSION = "commission"


class RevenueCalculator:
    """Handles revenue calculations and reporting."""
    
    def __init__(
        self,
        revenue_repo: RevenueEventRepository,
        conversion_repo: ConversionRepository,
        cache: CacheManager
    ):
        self.revenue_repo = revenue_repo
        self.conversion_repo = conversion_repo
        self.cache = cache
        self.cache_ttl = 600  # 10 minutes
    
    async def record_revenue_event(
        self,
        db: AsyncSession,
        event_data: RevenueEventCreate
    ) -> RevenueEvent:
        """Record a revenue event."""
        # Validate event type
        if event_data.event_type not in RevenueEventType:
            raise ValidationError(f"Invalid event type: {event_data.event_type}")
        
        # Validate amount based on event type
        if event_data.event_type in [RevenueEventType.REFUND, RevenueEventType.CHARGEBACK]:
            if event_data.amount > 0:
                event_data.amount = -abs(event_data.amount)
        
        # Create event
        event = await self.revenue_repo.create(db, event_data)
        
        # Update conversion if linked
        if event_data.conversion_id:
            await self._update_conversion_revenue(
                db, event_data.conversion_id, event_data.amount
            )
        
        # Invalidate caches
        await self._invalidate_revenue_caches(event_data.campaign_id)
        
        return event
    
    async def calculate_revenue_metrics(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_forecasts: bool = False
    ) -> RevenueMetrics:
        """Calculate comprehensive revenue metrics."""
        cache_key = f"revenue_metrics:{campaign_id}:{start_date}:{end_date}:{include_forecasts}"
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            return RevenueMetrics.model_validate_json(cached)
        
        # Build filters
        filters = [RevenueEvent.campaign_id == campaign_id]
        if start_date:
            filters.append(RevenueEvent.created_at >= start_date)
        if end_date:
            filters.append(RevenueEvent.created_at <= end_date)
        
        # Calculate base metrics
        base_metrics = await self._calculate_base_metrics(db, filters)
        
        # Get revenue breakdown
        breakdown = await self._calculate_revenue_breakdown(db, filters)
        
        # Calculate growth metrics
        growth_metrics = await self._calculate_growth_metrics(
            db, campaign_id, start_date, end_date
        )
        
        # Generate forecast if requested
        forecast = None
        if include_forecasts:
            forecast = await self._generate_revenue_forecast(
                db, campaign_id, base_metrics
            )
        
        metrics = RevenueMetrics(
            **base_metrics,
            **growth_metrics,
            breakdown=breakdown,
            forecast=forecast
        )
        
        # Cache result
        await self.cache.set(
            cache_key,
            metrics.model_dump_json(),
            expire=self.cache_ttl
        )
        
        return metrics
    
    async def generate_revenue_report(
        self,
        db: AsyncSession,
        campaign_ids: List[UUID],
        start_date: datetime,
        end_date: datetime,
        group_by: str = 'day'
    ) -> RevenueReport:
        """Generate detailed revenue report."""
        if not campaign_ids:
            raise BusinessLogicError("At least one campaign ID required")
        
        # Get revenue time series
        time_series = await self._get_revenue_time_series(
            db, campaign_ids, start_date, end_date, group_by
        )
        
        # Get revenue by event type
        event_breakdown = await self._get_revenue_by_event_type(
            db, campaign_ids, start_date, end_date
        )
        
        # Get top revenue sources
        top_sources = await self._get_top_revenue_sources(
            db, campaign_ids, start_date, end_date
        )
        
        # Calculate summary metrics
        summary = await self._calculate_summary_metrics(
            db, campaign_ids, start_date, end_date
        )
        
        return RevenueReport(
            period_start=start_date,
            period_end=end_date,
            campaigns=campaign_ids,
            summary=summary,
            time_series=time_series,
            event_breakdown=event_breakdown,
            top_sources=top_sources
        )
    
    async def calculate_roi(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        include_costs: bool = True
    ) -> Dict[str, Any]:
        """Calculate ROI for campaign."""
        # Get total revenue
        revenue_query = select(
            func.sum(RevenueEvent.amount)
        ).where(
            RevenueEvent.campaign_id == campaign_id
        )
        
        result = await db.execute(revenue_query)
        total_revenue = result.scalar() or Decimal('0')
        
        # Get campaign costs (would integrate with campaign service)
        total_cost = Decimal('0')
        if include_costs:
            # Placeholder - would get from campaign service
            total_cost = Decimal('1000')
        
        # Calculate ROI
        if total_cost > 0:
            roi = ((total_revenue - total_cost) / total_cost) * 100
        else:
            roi = Decimal('0')
        
        return {
            'total_revenue': float(total_revenue),
            'total_cost': float(total_cost),
            'net_profit': float(total_revenue - total_cost),
            'roi_percentage': float(roi),
            'profit_margin': float((total_revenue - total_cost) / total_revenue * 100) if total_revenue > 0 else 0
        }
    
    async def _calculate_base_metrics(
        self,
        db: AsyncSession,
        filters: List
    ) -> Dict[str, Any]:
        """Calculate base revenue metrics."""
        # Total revenue by type
        revenue_query = select(
            func.sum(
                case(
                    (RevenueEvent.event_type == RevenueEventType.CONVERSION, RevenueEvent.amount),
                    else_=0
                )
            ).label('gross_revenue'),
            func.sum(
                case(
                    (RevenueEvent.event_type.in_([RevenueEventType.REFUND, RevenueEventType.CHARGEBACK]), RevenueEvent.amount),
                    else_=0
                )
            ).label('refunds_chargebacks'),
            func.sum(RevenueEvent.amount).label('net_revenue'),
            func.count(RevenueEvent.id).label('total_events')
        ).where(and_(*filters))
        
        result = await db.execute(revenue_query)
        row = result.one()
        
        gross_revenue = float(row.gross_revenue or 0)
        refunds_chargebacks = abs(float(row.refunds_chargebacks or 0))
        net_revenue = float(row.net_revenue or 0)
        
        return {
            'gross_revenue': gross_revenue,
            'refunds': refunds_chargebacks,
            'net_revenue': net_revenue,
            'total_transactions': row.total_events or 0,
            'refund_rate': (refunds_chargebacks / gross_revenue * 100) if gross_revenue > 0 else 0
        }
    
    async def _calculate_revenue_breakdown(
        self,
        db: AsyncSession,
        filters: List
    ) -> RevenueBreakdown:
        """Calculate revenue breakdown by type."""
        breakdown_query = select(
            RevenueEvent.event_type,
            func.count(RevenueEvent.id).label('count'),
            func.sum(RevenueEvent.amount).label('amount')
        ).where(
            and_(*filters)
        ).group_by(RevenueEvent.event_type)
        
        result = await db.execute(breakdown_query)
        
        by_type = {}
        for row in result:
            by_type[row.event_type] = {
                'count': row.count,
                'amount': float(row.amount or 0)
            }
        
        # Get currency breakdown
        currency_query = select(
            RevenueEvent.currency,
            func.sum(RevenueEvent.amount).label('amount')
        ).where(
            and_(*filters)
        ).group_by(RevenueEvent.currency)
        
        currency_result = await db.execute(currency_query)
        
        by_currency = {
            row.currency: float(row.amount or 0)
            for row in currency_result
        }
        
        return RevenueBreakdown(
            by_event_type=by_type,
            by_currency=by_currency,
            by_source={}  # Would integrate with source tracking
        )
    
    async def _calculate_growth_metrics(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Calculate growth metrics."""
        if not start_date or not end_date:
            return {
                'growth_rate': 0,
                'average_order_value': 0
            }
        
        # Calculate period length
        period_days = (end_date - start_date).days
        
        # Get previous period metrics
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date
        
        current_revenue_query = select(
            func.sum(RevenueEvent.amount)
        ).where(
            and_(
                RevenueEvent.campaign_id == campaign_id,
                RevenueEvent.created_at >= start_date,
                RevenueEvent.created_at <= end_date
            )
        )
        
        prev_revenue_query = select(
            func.sum(RevenueEvent.amount)
        ).where(
            and_(
                RevenueEvent.campaign_id == campaign_id,
                RevenueEvent.created_at >= prev_start,
                RevenueEvent.created_at < prev_end
            )
        )
        
        current_result = await db.execute(current_revenue_query)
        prev_result = await db.execute(prev_revenue_query)
        
        current_revenue = current_result.scalar() or Decimal('0')
        prev_revenue = prev_result.scalar() or Decimal('0')
        
        # Calculate growth rate
        if prev_revenue > 0:
            growth_rate = ((current_revenue - prev_revenue) / prev_revenue) * 100
        else:
            growth_rate = Decimal('0')
        
        # Calculate AOV
        aov_query = select(
            func.avg(RevenueEvent.amount)
        ).where(
            and_(
                RevenueEvent.campaign_id == campaign_id,
                RevenueEvent.event_type == RevenueEventType.CONVERSION,
                RevenueEvent.created_at >= start_date,
                RevenueEvent.created_at <= end_date
            )
        )
        
        aov_result = await db.execute(aov_query)
        aov = aov_result.scalar() or Decimal('0')
        
        return {
            'growth_rate': float(growth_rate),
            'average_order_value': float(aov)
        }
    
    async def _generate_revenue_forecast(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        current_metrics: Dict[str, Any]
    ) -> RevenueForecast:
        """Generate revenue forecast."""
        # Simple forecast based on historical trends
        # In production, would use more sophisticated forecasting
        
        # Get last 30 days average
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        daily_avg_query = select(
            func.avg(RevenueEvent.amount)
        ).where(
            and_(
                RevenueEvent.campaign_id == campaign_id,
                RevenueEvent.created_at >= thirty_days_ago
            )
        )
        
        result = await db.execute(daily_avg_query)
        daily_avg = result.scalar() or Decimal('0')
        
        # Simple linear projection
        next_7_days = float(daily_avg) * 7
        next_30_days = float(daily_avg) * 30
        next_90_days = float(daily_avg) * 90
        
        return RevenueForecast(
            next_7_days=next_7_days,
            next_30_days=next_30_days,
            next_90_days=next_90_days,
            confidence_level=0.7,
            factors_considered=['historical_average', 'linear_projection']
        )
    
    async def _get_revenue_time_series(
        self,
        db: AsyncSession,
        campaign_ids: List[UUID],
        start_date: datetime,
        end_date: datetime,
        group_by: str
    ) -> List[Dict[str, Any]]:
        """Get revenue time series data."""
        # Determine date truncation
        if group_by == 'hour':
            date_trunc = func.date_trunc('hour', RevenueEvent.created_at)
        elif group_by == 'day':
            date_trunc = func.date_trunc('day', RevenueEvent.created_at)
        elif group_by == 'week':
            date_trunc = func.date_trunc('week', RevenueEvent.created_at)
        else:
            date_trunc = func.date_trunc('month', RevenueEvent.created_at)
        
        query = select(
            date_trunc.label('period'),
            func.sum(RevenueEvent.amount).label('revenue'),
            func.count(RevenueEvent.id).label('transactions')
        ).where(
            and_(
                RevenueEvent.campaign_id.in_(campaign_ids),
                RevenueEvent.created_at >= start_date,
                RevenueEvent.created_at <= end_date
            )
        ).group_by(date_trunc).order_by(date_trunc)
        
        result = await db.execute(query)
        
        return [
            {
                'period': row.period.isoformat(),
                'revenue': float(row.revenue or 0),
                'transactions': row.transactions
            }
            for row in result
        ]
    
    async def _update_conversion_revenue(
        self,
        db: AsyncSession,
        conversion_id: UUID,
        amount_change: Decimal
    ) -> None:
        """Update conversion revenue amount."""
        conversion = await self.conversion_repo.get(db, conversion_id)
        if conversion:
            new_amount = (conversion.revenue_amount or Decimal('0')) + amount_change
            await self.conversion_repo.update_revenue(
                db, conversion_id, new_amount
            )
    
    async def _invalidate_revenue_caches(self, campaign_id: UUID) -> None:
        """Invalidate revenue-related caches."""
        patterns = [
            f"revenue_metrics:{campaign_id}:*",
            f"conversion_metrics:{campaign_id}:*"
        ]
        
        await asyncio.gather(*[
            self.cache.delete_pattern(pattern)
            for pattern in patterns
        ])
    
    async def _get_revenue_by_event_type(
        self,
        db: AsyncSession,
        campaign_ids: List[UUID],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """Get revenue breakdown by event type."""
        query = select(
            RevenueEvent.event_type,
            func.count(RevenueEvent.id).label('count'),
            func.sum(RevenueEvent.amount).label('amount')
        ).where(
            and_(
                RevenueEvent.campaign_id.in_(campaign_ids),
                RevenueEvent.created_at >= start_date,
                RevenueEvent.created_at <= end_date
            )
        ).group_by(RevenueEvent.event_type)
        
        result = await db.execute(query)
        
        return {
            row.event_type: {
                'count': row.count,
                'amount': float(row.amount or 0)
            }
            for row in result
        }
    
    async def _get_top_revenue_sources(
        self,
        db: AsyncSession,
        campaign_ids: List[UUID],
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top revenue sources."""
        # This would integrate with source tracking
        # For now, return empty list
        return []
    
    async def _calculate_summary_metrics(
        self,
        db: AsyncSession,
        campaign_ids: List[UUID],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate summary metrics for report."""
        query = select(
            func.sum(RevenueEvent.amount).label('total_revenue'),
            func.count(RevenueEvent.id).label('total_transactions'),
            func.avg(RevenueEvent.amount).label('avg_transaction')
        ).where(
            and_(
                RevenueEvent.campaign_id.in_(campaign_ids),
                RevenueEvent.created_at >= start_date,
                RevenueEvent.created_at <= end_date
            )
        )
        
        result = await db.execute(query)
        row = result.one()
        
        return {
            'total_revenue': float(row.total_revenue or 0),
            'total_transactions': row.total_transactions or 0,
            'average_transaction_value': float(row.avg_transaction or 0)
        }