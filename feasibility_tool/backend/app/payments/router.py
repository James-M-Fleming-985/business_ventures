"""
Stripe Payment Routes for Feasibility Platform
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import stripe
import os

from ..database import get_db
from ..models import User, SubscriptionTier
from ..auth.dependencies import get_current_user, get_optional_user
from .stripe_service import get_stripe_service


router = APIRouter(
    prefix="/stripe",
    tags=["payments"],
)


class CheckoutSessionRequest(BaseModel):
    """Request to create checkout session"""
    tier: str = "pro"
    customer_email: Optional[EmailStr] = None


class PortalSessionRequest(BaseModel):
    """Request to create portal session"""
    return_url: str


@router.get("/tiers")
async def get_pricing_tiers():
    """Get available subscription tiers and pricing"""
    stripe_service = get_stripe_service()
    return stripe_service.get_tiers_info()


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Create Stripe Checkout session for Pro subscription.
    Can be called with or without authentication.
    """
    stripe_service = get_stripe_service()
    
    # Use current user's email if authenticated
    customer_email = request.customer_email
    if current_user:
        customer_email = current_user.email
    
    # Get frontend URL for success/cancel redirects
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    try:
        session = stripe_service.create_checkout_session(
            tier=request.tier,
            success_url=f"{frontend_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url}/pricing?canceled=true",
            customer_email=customer_email
        )
        
        return {"checkout_url": session.url}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.post("/create-portal-session")
async def create_portal_session(
    request: PortalSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create Stripe Customer Portal session for managing subscription.
    Requires authentication.
    """
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found"
        )
    
    stripe_service = get_stripe_service()
    
    try:
        session = stripe_service.create_portal_session(
            customer_id=current_user.stripe_customer_id,
            return_url=request.return_url
        )
        
        return {"portal_url": session.url}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create portal session: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    Processes subscription updates, payment successes, cancellations, etc.
    """
    stripe_service = get_stripe_service()
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if not webhook_secret:
        print("⚠️  WARNING: STRIPE_WEBHOOK_SECRET not set, skipping signature verification")
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        if webhook_secret and sig_header:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            event = stripe.Event.construct_from(
                await request.json(), stripe.api_key
            )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle different event types
    event_type = event["type"]
    
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        await handle_checkout_completed(session, db)
    
    elif event_type == "customer.subscription.updated":
        subscription = event["data"]["object"]
        await handle_subscription_updated(subscription, db)
    
    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        await handle_subscription_deleted(subscription, db)
    
    elif event_type == "invoice.payment_failed":
        invoice = event["data"]["object"]
        await handle_payment_failed(invoice, db)
    
    return {"status": "success"}


async def handle_checkout_completed(session: dict, db: Session):
    """Update user to Pro tier after successful checkout"""
    customer_id = session.get("customer")
    customer_email = session.get("customer_details", {}).get("email")
    subscription_id = session.get("subscription")
    
    if not customer_email:
        print(f"⚠️  No email in checkout session: {session.get('id')}")
        return
    
    # Find user by email
    user = db.query(User).filter(User.email == customer_email).first()
    if not user:
        print(f"⚠️  User not found for email: {customer_email}")
        return
    
    # Update user subscription
    user.stripe_customer_id = customer_id
    user.stripe_subscription_id = subscription_id
    user.subscription_tier = SubscriptionTier.PRO
    user.subscription_status = "active"
    user.monthly_explorations = 0  # Reset counter for Pro (not used but kept for tracking)
    
    db.commit()
    print(f"✅ User {user.email} upgraded to Pro")


async def handle_subscription_updated(subscription: dict, db: Session):
    """Handle subscription status changes"""
    subscription_id = subscription.get("id")
    status_value = subscription.get("status")
    
    user = db.query(User).filter(User.stripe_subscription_id == subscription_id).first()
    if not user:
        return
    
    user.subscription_status = status_value
    db.commit()
    print(f"✅ Subscription {subscription_id} updated to {status_value}")


async def handle_subscription_deleted(subscription: dict, db: Session):
    """Downgrade user to Free tier when subscription is canceled"""
    subscription_id = subscription.get("id")
    
    user = db.query(User).filter(User.stripe_subscription_id == subscription_id).first()
    if not user:
        return
    
    user.subscription_tier = SubscriptionTier.FREE
    user.subscription_status = "canceled"
    user.stripe_subscription_id = None
    
    db.commit()
    print(f"✅ User {user.email} downgraded to Free")


async def handle_payment_failed(invoice: dict, db: Session):
    """Handle failed payment - mark subscription as past_due"""
    subscription_id = invoice.get("subscription")
    
    user = db.query(User).filter(User.stripe_subscription_id == subscription_id).first()
    if not user:
        return
    
    user.subscription_status = "past_due"
    db.commit()
    print(f"⚠️  Payment failed for user {user.email}")
