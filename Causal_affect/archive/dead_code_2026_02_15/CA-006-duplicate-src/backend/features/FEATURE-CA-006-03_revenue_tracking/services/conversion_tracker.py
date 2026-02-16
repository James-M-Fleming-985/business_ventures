from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncio
from decimal import Decimal

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import json

from ..db.models import Conversion, RevenueEvent
from ..db.repositories import ConversionRepository, RevenueEventRepository
from ..models.schemas import (
    ConversionCreate,
    ConversionUpdate,
    ConversionStatus,
    ConversionMetrics,
    ConversionAnalytics
)
from core.exceptions import BusinessLogicError, NotFoundError
from core.cache import CacheManager


class ConversionTracker:
    """Handles conversion tracking and analytics."""
    
    def __init__(
        self,
        conversion_repo: ConversionRepository,
        revenue_repo: RevenueEventRepository,
        cache: CacheManager
    ):
        self.conversion_repo = conversion_repo
        self.revenue_repo = revenue_repo
        self.cache = cache
        self.cache_ttl = 300  # 5 minutes
    
    async def track_conversion(
        self,
        db: AsyncSession,
        conversion_data: ConversionCreate
    ) -> Conversion:
        """Track a new conversion event."""
        # Check for duplicate conversions
        existing = await self.conversion_repo.find_by_transaction_id(
            db, conversion_data.transaction_id
        )
        if existing:
            raise BusinessLogicError(
                f"Conversion already tracked for transaction {conversion_data.transaction_id}"
            )
        
        # Create conversion record
        conversion = await self.conversion_repo.create(db, conversion_data)
        
        # Invalidate related caches
        await self._invalidate_caches(conversion.campaign_id, conversion.customer_id)
        
        # Track revenue event if amount provided
        if conversion_data.revenue_amount:
            await self._create_revenue_event(db, conversion)
        
        return conversion
    
    async def update_conversion_status(
        self,
        db: AsyncSession,
        conversion_id: UUID,
        status: ConversionStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversion:
        """Update conversion status."""
        conversion = await self.conversion_repo.get(db, conversion_id)
        if not conversion:
            raise NotFoundError(f"Conversion {conversion_id} not found")
        
        update_data = ConversionUpdate(
            status=status,
            metadata=metadata or conversion.metadata
        )
        
        conversion = await self.conversion_repo.update(
            db, conversion_id, update_data
        )
        
        await self._invalidate_caches(conversion.campaign_id, conversion.customer_id)
        
        return conversion
    
    async def get_conversion_metrics(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ConversionMetrics:
        """Get conversion metrics for a campaign."""
        cache_key = f"conversion_metrics:{campaign_id}:{start_date}:{end_date}"
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            return ConversionMetrics.model_validate_json(cached)
        
        # Build date filter
        filters = [Conversion.campaign_id == campaign_id]
        if start_date:
            filters.append(Conversion.created_at >= start_date)
        if end_date:
            filters.append(Conversion.created_at <= end_date)
        
        # Get metrics
        metrics_query = select(
            func.count(Conversion.id).label('total_conversions'),
            func.count(func.distinct(Conversion.customer_id)).label('unique_customers'),
            func.sum(Conversion.revenue_amount).label('total_revenue'),
            func.avg(Conversion.revenue_amount).label('avg_revenue')
        ).where(and_(*filters))
        
        result = await db.execute(metrics_query)
        row = result.one()
        
        # Get conversion by status
        status_query = select(
            Conversion.status,
            func.count(Conversion.id).label('count')
        ).where(
            and_(*filters)
        ).group_by(Conversion.status)
        
        status_result = await db.execute(status_query)
        conversions_by_status = {
            row.status: row.count for row in status_result
        }
        
        metrics = ConversionMetrics(
            total_conversions=row.total_conversions or 0,
            unique_customers=row.unique_customers or 0,
            total_revenue=float(row.total_revenue or 0),
            average_revenue=float(row.avg_revenue or 0),
            conversion_rate=await self._calculate_conversion_rate(
                db, campaign_id, start_date, end_date
            ),
            conversions_by_status=conversions_by_status
        )
        
        # Cache result
        await self.cache.set(
            cache_key,
            metrics.model_dump_json(),
            expire=self.cache_ttl
        )
        
        return metrics
    
    async def get_conversion_analytics(
        self,
        db: AsyncSession,
        campaign_ids: List[UUID],
        group_by: str = 'day',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ConversionAnalytics:
        """Get conversion analytics across campaigns."""
        if not campaign_ids:
            raise BusinessLogicError("At least one campaign ID required")
        
        # Default date range
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get time series data
        time_series = await self._get_time_series_data(
            db, campaign_ids, group_by, start_date, end_date
        )
        
        # Get top converting products
        top_products = await self._get_top_products(
            db, campaign_ids, start_date, end_date
        )
        
        # Get conversion funnel
        funnel_data = await self._get_conversion_funnel(
            db, campaign_ids, start_date, end_date
        )
        
        return ConversionAnalytics(
            time_series=time_series,
            top_products=top_products,
            funnel_data=funnel_data,
            period_start=start_date,
            period_end=end_date
        )
    
    async def _create_revenue_event(
        self,
        db: AsyncSession,
        conversion: Conversion
    ) -> None:
        """Create revenue event for conversion."""
        from .revenue_calculator import RevenueEventType
        
        await self.revenue_repo.create(
            db,
            campaign_id=conversion.campaign_id,
            conversion_id=conversion.id,
            event_type=RevenueEventType.CONVERSION,
            amount=conversion.revenue_amount,
            currency=conversion.currency,
            metadata={
                'customer_id': str(conversion.customer_id),
                'product_id': conversion.product_id,
                'source': conversion.source
            }
        )
    
    async def _calculate_conversion_rate(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> float:
        """Calculate conversion rate for campaign."""
        # This would integrate with campaign tracking data
        # For now, return a placeholder
        return 0.0
    
    async def _get_time_series_data(
        self,
        db: AsyncSession,
        campaign_ids: List[UUID],
        group_by: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get time series conversion data."""
        # Group by date truncation based on parameter
        if group_by == 'hour':
            date_trunc = func.date_trunc('hour', Conversion.created_at)
        elif group_by == 'day':
            date_trunc = func.date_trunc('day', Conversion.created_at)
        elif group_by == 'week':
            date_trunc = func.date_trunc('week', Conversion.created_at)
        else:
            date_trunc = func.date_trunc('month', Conversion.created_at)
        
        query = select(
            date_trunc.label('period'),
            func.count(Conversion.id).label('conversions'),
            func.sum(Conversion.revenue_amount).label('revenue')
        ).where(
            and_(
                Conversion.campaign_id.in_(campaign_ids),
                Conversion.created_at >= start_date,
                Conversion.created_at <= end_date
            )
        ).group_by(date_trunc).order_by(date_trunc)
        
        result = await db.execute(query)
        
        return [
            {
                'period': row.period.isoformat(),
                'conversions': row.conversions,
                'revenue': float(row.revenue or 0)
            }
            for row in result
        ]
    
    async def _get_top_products(
        self,
        db: AsyncSession,
        campaign_ids: List[UUID],
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top converting products."""
        query = select(
            Conversion.product_id,
            func.count(Conversion.id).label('conversions'),
            func.sum(Conversion.revenue_amount).label('revenue')
        ).where(
            and_(
                Conversion.campaign_id.in_(campaign_ids),
                Conversion.created_at >= start_date,
                Conversion.created_at <= end_date,
                Conversion.product_id.isnot(None)
            )
        ).group_by(
            Conversion.product_id
        ).order_by(
            func.sum(Conversion.revenue_amount).desc()
        ).limit(limit)
        
        result = await db.execute(query)
        
        return [
            {
                'product_id': row.product_id,
                'conversions': row.conversions,
                'revenue': float(row.revenue or 0)
            }
            for row in result
        ]
    
    async def _get_conversion_funnel(
        self,
        db: AsyncSession,
        campaign_ids: List[UUID],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, int]:
        """Get conversion funnel data."""
        base_filter = and_(
            Conversion.campaign_id.in_(campaign_ids),
            Conversion.created_at >= start_date,
            Conversion.created_at <= end_date
        )
        
        # Count conversions by status
        status_counts = {}
        for status in ConversionStatus:
            count_query = select(
                func.count(Conversion.id)
            ).where(
                and_(base_filter, Conversion.status == status)
            )
            result = await db.execute(count_query)
            status_counts[status.value] = result.scalar() or 0
        
        return status_counts
    
    async def _invalidate_caches(self, campaign_id: UUID, customer_id: UUID) -> None:
        """Invalidate related caches."""
        patterns = [
            f"conversion_metrics:{campaign_id}:*",
            f"revenue_metrics:{campaign_id}:*",
            f"customer_conversions:{customer_id}:*"
        ]
        
        await asyncio.gather(*[
            self.cache.delete_pattern(pattern)
            for pattern in patterns
        ])