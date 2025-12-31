"""
Subscription Enforcement Middleware
Checks user subscription limits for API endpoints
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models import User, SubscriptionTier


class SubscriptionLimits:
    """Subscription tier limits"""
    FREE_EXPLORATIONS_PER_MONTH = 5
    PRO_EXPLORATIONS_PER_MONTH = -1  # Unlimited


async def check_exploration_limit(user: User, db: Session) -> None:
    """
    Check if user has reached their monthly exploration limit.
    Raises HTTPException if limit exceeded.
    
    Args:
        user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: 402 Payment Required if limit exceeded
    """
    # Pro users have unlimited explorations
    if user.subscription_tier == SubscriptionTier.PRO:
        return
    
    # Check if we need to reset the monthly counter
    now = datetime.utcnow()
    if user.monthly_explorations_reset_date is None or user.monthly_explorations_reset_date < now:
        # Reset counter for new month
        user.monthly_explorations = 0
        user.monthly_explorations_reset_date = now + timedelta(days=30)
        db.commit()
    
    # Check if user has exceeded free tier limit
    if user.monthly_explorations >= SubscriptionLimits.FREE_EXPLORATIONS_PER_MONTH:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": "Monthly exploration limit reached",
                "limit": SubscriptionLimits.FREE_EXPLORATIONS_PER_MONTH,
                "current": user.monthly_explorations,
                "tier": "free",
                "upgrade_url": "/pricing"
            }
        )


async def increment_exploration_count(user: User, db: Session) -> None:
    """
    Increment user's monthly exploration count.
    
    Args:
        user: Current authenticated user
        db: Database session
    """
    user.monthly_explorations += 1
    db.commit()


def get_user_usage_stats(user: User) -> dict:
    """
    Get user's current usage statistics.
    
    Args:
        user: User object
        
    Returns:
        Dictionary with usage stats
    """
    if user.subscription_tier == SubscriptionTier.PRO:
        return {
            "tier": "pro",
            "explorations_used": user.monthly_explorations,
            "explorations_limit": -1,  # Unlimited
            "explorations_remaining": -1,  # Unlimited
            "reset_date": None
        }
    
    return {
        "tier": "free",
        "explorations_used": user.monthly_explorations,
        "explorations_limit": SubscriptionLimits.FREE_EXPLORATIONS_PER_MONTH,
        "explorations_remaining": max(0, SubscriptionLimits.FREE_EXPLORATIONS_PER_MONTH - user.monthly_explorations),
        "reset_date": user.monthly_explorations_reset_date.isoformat() if user.monthly_explorations_reset_date else None
    }
