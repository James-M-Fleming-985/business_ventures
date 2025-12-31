"""
Stripe Service for Feasibility Platform
Handles payment processing and subscriptions
"""
import stripe
import os
from typing import Dict, Any, Optional
from datetime import datetime


class StripeService:
    """Service for handling Stripe payment operations"""
    
    # Pricing configuration
    TIERS = {
        "free": {
            "name": "Free",
            "price": 0,
            "currency": "GBP",
            "explorations_per_month": 5,
            "features": [
                "5 feasibility explorations per month",
                "Basic visualizations",
                "Baseline comparison",
                "Export results"
            ]
        },
        "pro": {
            "name": "Pro",
            "price": 9.99,
            "currency": "GBP",
            "price_id": os.getenv("STRIPE_PRICE_ID_PRO", "price_placeholder"),
            "explorations_per_month": -1,  # Unlimited
            "features": [
                "Unlimited feasibility explorations",
                "Advanced visualizations (all 9 modes)",
                "Multiple baselines",
                "Exploration history export",
                "Priority support",
                "API access"
            ]
        }
    }
    
    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not self.api_key or self.api_key.startswith("sk_test_placeholder"):
            print("⚠️  WARNING: Using placeholder Stripe API key. Please set STRIPE_SECRET_KEY in environment")
            print("   Get your keys from: https://dashboard.stripe.com/test/apikeys")
        stripe.api_key = self.api_key
    
    def create_checkout_session(
        self,
        tier: str,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None
    ) -> stripe.checkout.Session:
        """Create a Stripe Checkout session for Pro subscription (£9.99/month)"""
        
        if tier != "pro":
            raise ValueError("Only Pro tier subscriptions are available")
        
        tier_config = self.TIERS["pro"]
        
        session_params = {
            "mode": "subscription",
            "line_items": [
                {
                    "price": tier_config["price_id"],
                    "quantity": 1,
                }
            ],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "allow_promotion_codes": True,
            "billing_address_collection": "auto",
            "metadata": {
                "tier": tier,
                "platform": "feasibility_tool"
            }
        }
        
        if customer_email:
            session_params["customer_email"] = customer_email
        
        return stripe.checkout.Session.create(**session_params)
    
    def create_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> stripe.billing_portal.Session:
        """Create a Customer Portal session for managing subscriptions"""
        return stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
    
    def get_tiers_info(self) -> Dict[str, Any]:
        """Get pricing tiers information"""
        return {
            "tiers": [
                {
                    "tier": "free",
                    "name": self.TIERS["free"]["name"],
                    "price": self.TIERS["free"]["price"],
                    "currency": self.TIERS["free"]["currency"],
                    "interval": None,
                    "features": self.TIERS["free"]["features"],
                    "explorations_per_month": self.TIERS["free"]["explorations_per_month"],
                    "is_popular": False
                },
                {
                    "tier": "pro",
                    "name": self.TIERS["pro"]["name"],
                    "price": self.TIERS["pro"]["price"],
                    "currency": self.TIERS["pro"]["currency"],
                    "interval": "month",
                    "features": self.TIERS["pro"]["features"],
                    "explorations_per_month": self.TIERS["pro"]["explorations_per_month"],
                    "is_popular": True
                }
            ]
        }
    
    async def handle_checkout_completed(
        self, 
        session: Dict[str, Any],
        db_update_callback
    ) -> None:
        """Handle successful checkout - user subscribed to Pro (£9.99/month)"""
        customer_id = session.get("customer")
        customer_email = session.get("customer_email") or \
                        session.get("customer_details", {}).get("email")
        subscription_id = session.get("subscription")
        
        print(f"✅ New Pro subscription: {customer_email}")
        print(f"   Customer ID: {customer_id}")
        print(f"   Subscription ID: {subscription_id}")
        
        # Call database update callback
        if db_update_callback:
            await db_update_callback({
                "customer_id": customer_id,
                "subscription_id": subscription_id,
                "tier": "pro",
                "status": "active"
            })
    
    async def handle_subscription_updated(
        self, 
        subscription: Dict[str, Any],
        db_update_callback
    ) -> None:
        """Handle subscription update (renewal, etc.)"""
        customer_id = subscription.get("customer")
        subscription_id = subscription.get("id")
        status = subscription.get("status")
        
        print(f"🔄 Subscription updated: {subscription_id}")
        print(f"   Customer: {customer_id}")
        print(f"   Status: {status}")
        
        if db_update_callback:
            await db_update_callback({
                "subscription_id": subscription_id,
                "status": status
            })
    
    async def handle_subscription_deleted(
        self, 
        subscription: Dict[str, Any],
        db_update_callback
    ) -> None:
        """Handle subscription cancellation"""
        customer_id = subscription.get("customer")
        subscription_id = subscription.get("id")
        
        print(f"❌ Subscription canceled: {subscription_id}")
        print(f"   Customer: {customer_id}")
        
        if db_update_callback:
            await db_update_callback({
                "subscription_id": subscription_id,
                "tier": "free",
                "status": "canceled"
            })


# Singleton instance
_stripe_service = None

def get_stripe_service() -> StripeService:
    """Get or create Stripe service instance"""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService()
    return _stripe_service
