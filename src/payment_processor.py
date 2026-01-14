"""Production Stripe Payment Processor with webhooks and subscription management."""
import os
import stripe
import logging
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class SubscriptionTier(Enum):
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class PricingPlan:
    """Pricing tier definitions."""
    PLANS = {
        SubscriptionTier.STARTER: {
            "name": "Starter",
            "price": 4900,  # $49.00 in cents
            "interval": "month",
            "features": ["10GB data", "5 pipelines", "Email support"]
        },
        SubscriptionTier.PRO: {
            "name": "Pro",
            "price": 19900,  # $199.00
            "interval": "month",
            "features": ["100GB data", "Unlimited pipelines", "Priority support"]
        },
        SubscriptionTier.ENTERPRISE: {
            "name": "Enterprise",
            "price": 49900,  # $499.00
            "interval": "month",
            "features": ["Unlimited data", "Custom integrations", "Dedicated support"]
        }
    }

class PaymentProcessor:
    """Handles all Stripe payment operations."""
    
    def __init__(self):
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    def create_customer(self, email: str, name: str, metadata: Dict = None) -> Dict:
        """Create Stripe customer."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {},
            )
            logger.info(f"Customer created: {customer.id}")
            return {"success": True, "customer_id": customer.id, "customer": customer}
        except stripe.error.StripeError as e:
            logger.error(f"Customer creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: Optional[int] = None
    ) -> Dict:
        """Create subscription for customer."""
        try:
            params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "payment_behavior": "default_incomplete",
                "expand": ["latest_invoice.payment_intent"],
            }
            
            if trial_days:
                params["trial_period_days"] = trial_days
            
            subscription = stripe.Subscription.create(**params)
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret,
                "status": subscription.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Subscription creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def cancel_subscription(self, subscription_id: str, immediate: bool = False) -> Dict:
        """Cancel subscription."""
        try:
            if immediate:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "status": subscription.status,
                "canceled_at": subscription.canceled_at
            }
        except stripe.error.StripeError as e:
            logger.error(f"Subscription cancellation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def update_subscription(self, subscription_id: str, new_price_id: str) -> Dict:
        """Upgrade/downgrade subscription."""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            updated = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription['items'].data[0].id,
                    "price": new_price_id,
                }],
                proration_behavior="create_prorations"
            )
            
            return {
                "success": True,
                "subscription_id": updated.id,
                "status": updated.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Subscription update failed: {e}")
            return {"success": False, "error": str(e)}
    
    def create_payment_intent(self, amount: int, currency: str = "usd", customer_id: str = None) -> Dict:
        """Create one-time payment intent."""
        try:
            params = {
                "amount": amount,
                "currency": currency,
                "automatic_payment_methods": {"enabled": True},
            }
            
            if customer_id:
                params["customer"] = customer_id
            
            intent = stripe.PaymentIntent.create(**params)
            
            return {
                "success": True,
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
            }
        except stripe.error.StripeError as e:
            logger.error(f"Payment intent creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def verify_webhook(self, payload: bytes, sig_header: str) -> Optional[Dict]:
        """Verify and parse Stripe webhook."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return None
    
    def handle_webhook_event(self, event: Dict) -> Dict:
        """Process webhook event."""
        event_type = event['type']
        
        handlers = {
            'payment_intent.succeeded': self._handle_payment_succeeded,
            'payment_intent.payment_failed': self._handle_payment_failed,
            'customer.subscription.created': self._handle_subscription_created,
            'customer.subscription.updated': self._handle_subscription_updated,
            'customer.subscription.deleted': self._handle_subscription_deleted,
            'invoice.payment_succeeded': self._handle_invoice_paid,
            'invoice.payment_failed': self._handle_invoice_failed,
        }
        
        handler = handlers.get(event_type)
        if handler:
            return handler(event['data']['object'])
        else:
            logger.info(f"Unhandled event type: {event_type}")
            return {"success": True, "message": "Event received but not processed"}
    
    def _handle_payment_succeeded(self, payment_intent: Dict) -> Dict:
        """Handle successful payment."""
        logger.info(f"Payment succeeded: {payment_intent['id']}")
        # TODO: Activate service, send confirmation email
        return {"success": True, "action": "activate_service"}
    
    def _handle_payment_failed(self, payment_intent: Dict) -> Dict:
        """Handle failed payment."""
        logger.warning(f"Payment failed: {payment_intent['id']}")
        # TODO: Send payment failed email, suspend service
        return {"success": True, "action": "suspend_service"}
    
    def _handle_subscription_created(self, subscription: Dict) -> Dict:
        """Handle new subscription."""
        logger.info(f"Subscription created: {subscription['id']}")
        return {"success": True, "action": "provision_resources"}
    
    def _handle_subscription_updated(self, subscription: Dict) -> Dict:
        """Handle subscription update."""
        logger.info(f"Subscription updated: {subscription['id']}")
        return {"success": True, "action": "update_resources"}
    
    def _handle_subscription_deleted(self, subscription: Dict) -> Dict:
        """Handle subscription cancellation."""
        logger.info(f"Subscription deleted: {subscription['id']}")
        return {"success": True, "action": "deprovision_resources"}
    
    def _handle_invoice_paid(self, invoice: Dict) -> Dict:
        """Handle successful invoice payment."""
        logger.info(f"Invoice paid: {invoice['id']}")
        return {"success": True, "action": "extend_subscription"}
    
    def _handle_invoice_failed(self, invoice: Dict) -> Dict:
        """Handle failed invoice payment."""
        logger.warning(f"Invoice payment failed: {invoice['id']}")
        return {"success": True, "action": "notify_payment_failure"}
    
    def get_customer_subscriptions(self, customer_id: str) -> List[Dict]:
        """Get all subscriptions for customer."""
        try:
            subscriptions = stripe.Subscription.list(customer=customer_id)
            return subscriptions.data
        except stripe.error.StripeError as e:
            logger.error(f"Failed to fetch subscriptions: {e}")
            return []
    
    def create_portal_session(self, customer_id: str, return_url: str) -> Dict:
        """Create customer portal session for managing subscriptions."""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return {"success": True, "url": session.url}
        except stripe.error.StripeError as e:
            logger.error(f"Portal session creation failed: {e}")
            return {"success": False, "error": str(e)}
