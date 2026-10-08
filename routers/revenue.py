"""
Revenue Dashboard Router (M1 Track E)

Provides /revenue/dashboard endpoint aggregating MRR, subscriber count,
and per-app breakdown from the revenue_events table.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func, case, and_
from sqlalchemy.orm import Session

from database import get_db
from models import RevenueEvent, User

from services.auth import require_admin

router = APIRouter(prefix="/revenue", tags=["revenue"], dependencies=[Depends(require_admin)])


@router.get("/dashboard")
def revenue_dashboard(
    months: int = 12,
    db: Session = Depends(get_db),
):
    """Aggregate revenue metrics across all apps.

    Returns:
        - current_mrr: Monthly Recurring Revenue in dollars
        - total_subscribers: Active paying subscribers
        - mrr_history: Monthly MRR for the last N months
        - per_app: Breakdown by app_id
        - recent_events: Last 20 revenue events
    """
    now = datetime.utcnow()
    lookback = now - timedelta(days=months * 31)

    # --- Current MRR ---
    # MRR = sum of most recent subscription_created/subscription_updated amounts
    # for subscriptions that have NOT been cancelled.
    # Simplified: sum all positive events in last 30 days minus cancellations.
    thirty_days_ago = now - timedelta(days=30)
    recent_revenue = (
        db.query(func.coalesce(func.sum(RevenueEvent.amount_cents), 0))
        .filter(
            RevenueEvent.event_at >= thirty_days_ago,
            RevenueEvent.event_type.in_(["subscription_created", "payment_succeeded", "subscription_updated"]),
        )
        .scalar()
    )
    current_mrr = round((recent_revenue or 0) / 100, 2)

    # --- Active subscribers ---
    # Count distinct users with subscription_created/updated but no recent cancellation
    active_subs = (
        db.query(User)
        .filter(
            User.subscription_tier != "free",
            User.subscription_expires_at > now,
        )
        .count()
    )

    # --- MRR history (monthly bucketed) ---
    mrr_history = []
    for i in range(months - 1, -1, -1):
        month_start = (now - timedelta(days=i * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)

        month_total = (
            db.query(func.coalesce(func.sum(RevenueEvent.amount_cents), 0))
            .filter(
                RevenueEvent.event_at >= month_start,
                RevenueEvent.event_at < month_end,
                RevenueEvent.event_type.in_(["subscription_created", "payment_succeeded", "subscription_updated"]),
            )
            .scalar()
        )
        mrr_history.append({
            "month": month_start.strftime("%Y-%m"),
            "mrr": round((month_total or 0) / 100, 2),
        })

    # --- Per-app breakdown ---
    per_app = (
        db.query(
            RevenueEvent.app_id,
            func.coalesce(func.sum(RevenueEvent.amount_cents), 0).label("total_cents"),
            func.count(RevenueEvent.id).label("event_count"),
        )
        .filter(RevenueEvent.event_at >= lookback)
        .group_by(RevenueEvent.app_id)
        .all()
    )
    per_app_data = [
        {
            "app_id": row.app_id,
            "total_revenue": round(row.total_cents / 100, 2),
            "event_count": row.event_count,
        }
        for row in per_app
    ]

    # --- Recent events ---
    recent = (
        db.query(RevenueEvent)
        .order_by(RevenueEvent.event_at.desc())
        .limit(20)
        .all()
    )

    return {
        "current_mrr": current_mrr,
        "total_subscribers": active_subs,
        "mrr_history": mrr_history,
        "per_app": per_app_data,
        "recent_events": [e.to_dict() for e in recent],
        "generated_at": now.isoformat(),
    }
