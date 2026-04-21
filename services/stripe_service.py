"""
Stripe Subscription Service for Causal Affect Platform
Handles subscription management, webhooks, and billing
"""

import os
import stripe
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from models import User, RevenueEvent

logger = logging.getLogger(__name__)

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

# Price IDs (set these in Railway environment variables)
PRICE_IDS = {
    "pro_monthly": os.getenv("STRIPE_PRICE_PRO_MONTHLY"),
    "pro_yearly": os.getenv("STRIPE_PRICE_PRO_YEARLY"),
    "enterprise_monthly": os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY"),
    "enterprise_yearly": os.getenv("STRIPE_PRICE_ENTERPRISE_YEARLY"),
}

# Tier mapping
TIER_FROM_PRICE = {}
for tier, price_id in PRICE_IDS.items():
    if price_id:
        TIER_FROM_PRICE[price_id] = tier.split("_")[0]  # 'pro' or 'enterprise'


def get_stripe_publishable_key() -> str:
    """Get Stripe publishable key for frontend"""
    return STRIPE_PUBLISHABLE_KEY or ""


def create_or_get_customer(db: Session, user: User) -> str:
    """Create or get existing Stripe customer for user"""
    if user.stripe_customer_id:
        return user.stripe_customer_id
    
    # Create new Stripe customer
    customer = stripe.Customer.create(
        email=user.email,
        name=user.display_name,
        metadata={"user_id": str(user.id)}
    )
    
    # Save customer ID to user
    user.stripe_customer_id = customer.id
    db.commit()
    
    logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
    return customer.id


def create_checkout_session(
    db: Session,
    user: User,
    price_id: str,
    success_url: str,
    cancel_url: str
) -> Dict[str, Any]:
    """Create a Stripe Checkout session for subscription"""
    customer_id = create_or_get_customer(db, user)
    
    checkout_session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": str(user.id)},
        subscription_data={
            "metadata": {"user_id": str(user.id)}
        }
    )
    
    return {
        "checkout_url": checkout_session.url,
        "session_id": checkout_session.id
    }


def create_billing_portal_session(
    db: Session,
    user: User,
    return_url: str
) -> str:
    """Create a Stripe Billing Portal session for managing subscription"""
    if not user.stripe_customer_id:
        raise ValueError("User has no Stripe customer ID")
    
    portal_session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=return_url
    )
    
    return portal_session.url


def handle_checkout_completed(
    db: Session,
    session: stripe.checkout.Session
) -> bool:
    """Handle successful checkout completion"""
    user_id = session.metadata.get("user_id")
    if not user_id:
        logger.error("No user_id in checkout session metadata")
        return False
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        logger.error(f"User {user_id} not found")
        return False
    
    # Get subscription details
    subscription_id = session.subscription
    subscription = stripe.Subscription.retrieve(subscription_id)
    
    # Determine tier from price
    price_id = subscription["items"]["data"][0]["price"]["id"]
    tier = TIER_FROM_PRICE.get(price_id, "pro")
    
    # Update user subscription
    user.subscription_tier = tier
    user.subscription_expires_at = datetime.fromtimestamp(
        subscription["current_period_end"]
    )
    user.stripe_customer_id = session.customer
    
    db.commit()
    logger.info(f"User {user.id} subscribed to {tier}")
    return True


def handle_subscription_updated(
    db: Session,
    subscription: stripe.Subscription
) -> bool:
    """Handle subscription updates (upgrade/downgrade/renewal)"""
    user_id = subscription.metadata.get("user_id")
    if not user_id:
        # Try to find by customer ID
        customer_id = subscription.customer
        user = db.query(User).filter(
            User.stripe_customer_id == customer_id
        ).first()
    else:
        user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user:
        logger.error(f"Could not find user for subscription {subscription.id}")
        return False
    
    # Determine tier from price
    price_id = subscription["items"]["data"][0]["price"]["id"]
    tier = TIER_FROM_PRICE.get(price_id, "pro")
    
    # Update user
    user.subscription_tier = tier
    user.subscription_expires_at = datetime.fromtimestamp(
        subscription["current_period_end"]
    )
    
    db.commit()
    logger.info(f"User {user.id} subscription updated to {tier}")
    return True


def handle_subscription_deleted(
    db: Session,
    subscription: stripe.Subscription
) -> bool:
    """Handle subscription cancellation"""
    customer_id = subscription.customer
    
    user = db.query(User).filter(
        User.stripe_customer_id == customer_id
    ).first()
    
    if not user:
        logger.error(f"Could not find user for customer {customer_id}")
        return False
    
    # Downgrade to free tier
    user.subscription_tier = "free"
    user.subscription_expires_at = None
    
    db.commit()
    logger.info(f"User {user.id} subscription cancelled, downgraded to free")
    return True


def _log_revenue_event(db: Session, event: dict, event_type: str, data: dict) -> None:
    """Log a Stripe event to the revenue_events table for MRR tracking."""
    stripe_event_id = event.get("id")
    if not stripe_event_id:
        return

    # Avoid duplicate inserts (idempotency via stripe_event_id unique constraint)
    existing = db.query(RevenueEvent).filter(
        RevenueEvent.stripe_event_id == stripe_event_id
    ).first()
    if existing:
        return

    # Extract financial details
    amount_cents = 0
    currency = "usd"
    tier = None
    interval = None
    stripe_customer_id = None
    stripe_subscription_id = None
    user_id = None

    if "customer" in data:
        stripe_customer_id = data["customer"] if isinstance(data["customer"], str) else data.get("customer")
    if "subscription" in data:
        stripe_subscription_id = data["subscription"] if isinstance(data["subscription"], str) else None

    # Map Stripe event types to our event_type taxonomy
    revenue_event_type = {
        "checkout.session.completed": "subscription_created",
        "customer.subscription.updated": "subscription_updated",
        "customer.subscription.deleted": "subscription_cancelled",
        "invoice.payment_failed": "payment_failed",
        "invoice.payment_succeeded": "payment_succeeded",
    }.get(event_type, event_type)

    # Extract amount from invoice events
    if "amount_total" in data:
        amount_cents = data["amount_total"] or 0
    elif "amount_paid" in data:
        amount_cents = data["amount_paid"] or 0
    if "currency" in data:
        currency = data["currency"] or "usd"

    # Try to resolve user
    if stripe_customer_id:
        user = db.query(User).filter(User.stripe_customer_id == stripe_customer_id).first()
        if user:
            user_id = user.id

    # Get subscription tier/interval if available
    if hasattr(data, "get") and data.get("items", {}).get("data"):
        item = data["items"]["data"][0]
        price_id = item.get("price", {}).get("id")
        tier = TIER_FROM_PRICE.get(price_id)
        interval = item.get("price", {}).get("recurring", {}).get("interval")

    event_at = datetime.utcfromtimestamp(event.get("created", 0)) if event.get("created") else datetime.utcnow()

    # PR5: bind to the most recent ProductDeployment build for this app so
    # revenue is attributable to the exact build iteration that earned it.
    build_id = None
    try:
        from models import ProductDeployment  # local import to avoid cycles
        dep = (
            db.query(ProductDeployment)
            .filter(ProductDeployment.app_id == "causal_affect")
            .order_by(ProductDeployment.deployed_at.desc().nullslast())
            .first()
        )
        if dep is not None:
            build_id = dep.build_id
    except Exception as exc:  # pragma: no cover — never block webhook on this
        logger.warning("PR5: could not resolve build_id for revenue event: %s", exc)

    rev = RevenueEvent(
        app_id="causal_affect",
        build_id=build_id,
        event_type=revenue_event_type,
        amount_cents=amount_cents,
        currency=currency,
        stripe_event_id=stripe_event_id,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id,
        user_id=user_id,
        tier=tier,
        interval=interval,
        event_at=event_at,
    )
    db.add(rev)
    db.commit()


def handle_webhook_event(db: Session, payload: bytes, sig_header: str) -> bool:
    """Process Stripe webhook events"""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        return False
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        return False
    
    event_type = event["type"]
    data = event["data"]["object"]
    
    logger.info(f"Processing Stripe webhook: {event_type}")
    
    # Log revenue event for all webhook types
    try:
        _log_revenue_event(db, event, event_type, data)
    except Exception as e:
        logger.warning(f"Failed to log revenue event: {e}")

    # Aggregate revenue into ProductMetrics for commercial intelligence (Track G)
    try:
        from services.commercial_intelligence_service import aggregate_revenue_to_metrics
        # Use 'causal_affect' as the default app_id for the platform itself
        app_id = "causal_affect"
        if event_type in ("invoice.payment_succeeded", "customer.subscription.updated",
                          "customer.subscription.deleted", "checkout.session.completed"):
            aggregate_revenue_to_metrics(db, app_id)
    except Exception as e:
        logger.warning(f"Failed to aggregate revenue to ProductMetrics: {e}")

    if event_type == "checkout.session.completed":
        return handle_checkout_completed(db, data)
    elif event_type == "customer.subscription.updated":
        return handle_subscription_updated(db, data)
    elif event_type == "customer.subscription.deleted":
        return handle_subscription_deleted(db, data)
    elif event_type == "invoice.payment_failed":
        logger.warning(f"Payment failed for invoice {data['id']}")
        return True
    else:
        logger.info(f"Unhandled webhook event type: {event_type}")
        return True


def get_subscription_status(user: User) -> Dict[str, Any]:
    """Get user's subscription status"""
    is_active = user.has_active_subscription
    days_remaining = None
    
    if user.subscription_expires_at:
        delta = user.subscription_expires_at - datetime.utcnow()
        days_remaining = max(0, delta.days)
        if days_remaining == 0:
            is_active = user.subscription_tier == "free"
    
    return {
        "tier": user.subscription_tier,
        "is_active": is_active,
        "expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
        "days_remaining": days_remaining,
        "has_stripe_customer": bool(user.stripe_customer_id)
    }
