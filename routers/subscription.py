"""
Subscription Router for Causal Affect Platform
Handles Stripe subscriptions, checkout, and webhooks
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database import get_db
from models import User
from services.auth import require_auth, get_current_user
from services.stripe_service import (
    get_stripe_publishable_key,
    create_checkout_session,
    create_billing_portal_session,
    handle_webhook_event,
    get_subscription_status,
    PRICE_IDS
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscription", tags=["Subscription"])


@router.get("/config")
async def get_subscription_config():
    """Get Stripe configuration for frontend"""
    return {
        "publishable_key": get_stripe_publishable_key(),
        "prices": {
            "pro": {
                "monthly": PRICE_IDS.get("pro_monthly"),
                "yearly": PRICE_IDS.get("pro_yearly"),
                "monthly_price": "£29",
                "yearly_price": "£290"
            },
            "enterprise": {
                "monthly": PRICE_IDS.get("enterprise_monthly"),
                "yearly": PRICE_IDS.get("enterprise_yearly"),
                "monthly_price": "£99",
                "yearly_price": "£990"
            }
        }
    }


@router.get("/status")
async def get_status(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get current user's subscription status"""
    return get_subscription_status(current_user)


@router.post("/checkout")
async def create_checkout(
    request: Request,
    tier: str,
    billing_period: str = "monthly",
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session for subscription"""
    # Validate tier
    if tier not in ["pro", "enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription tier"
        )
    
    # Validate billing period
    if billing_period not in ["monthly", "yearly"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid billing period"
        )
    
    # Get price ID
    price_key = f"{tier}_{billing_period}"
    price_id = PRICE_IDS.get(price_key)
    
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe not configured. Please contact support."
        )
    
    # Build URLs
    base_url = str(request.base_url).rstrip("/")
    success_url = f"{base_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}/subscription/cancel"
    
    try:
        result = create_checkout_session(
            db=db,
            user=current_user,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url
        )
        return result
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.get("/portal")
async def get_billing_portal(
    request: Request,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get Stripe billing portal URL for subscription management"""
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found"
        )
    
    base_url = str(request.base_url).rstrip("/")
    return_url = f"{base_url}/dashboard"
    
    try:
        portal_url = create_billing_portal_session(
            db=db,
            user=current_user,
            return_url=return_url
        )
        return {"portal_url": portal_url}
    except Exception as e:
        logger.error(f"Portal error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )
    
    success = handle_webhook_event(db, payload, sig_header)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook processing failed"
        )
    
    return {"status": "ok"}
