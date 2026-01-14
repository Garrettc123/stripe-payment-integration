"""FastAPI server for payment processing."""
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from payment_processor import PaymentProcessor, SubscriptionTier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Payment Processing API", version="1.0.0")
processor = PaymentProcessor()

class CustomerCreate(BaseModel):
    email: EmailStr
    name: str

class SubscriptionCreate(BaseModel):
    customer_id: str
    tier: SubscriptionTier
    trial_days: Optional[int] = None

class PaymentIntentCreate(BaseModel):
    amount: int
    currency: str = "usd"
    customer_id: Optional[str] = None

@app.post("/api/v1/customers")
async def create_customer(customer: CustomerCreate):
    """Create new customer."""
    result = processor.create_customer(
        email=customer.email,
        name=customer.name,
        metadata={"source": "api"}
    )
    
    if result["success"]:
        return JSONResponse(content=result, status_code=201)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.post("/api/v1/subscriptions")
async def create_subscription(subscription: SubscriptionCreate):
    """Create new subscription."""
    # TODO: Get price_id from tier (need to create products in Stripe first)
    price_id = f"price_{subscription.tier.value}"  # Placeholder
    
    result = processor.create_subscription(
        customer_id=subscription.customer_id,
        price_id=price_id,
        trial_days=subscription.trial_days
    )
    
    if result["success"]:
        return JSONResponse(content=result, status_code=201)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.delete("/api/v1/subscriptions/{subscription_id}")
async def cancel_subscription(subscription_id: str, immediate: bool = False):
    """Cancel subscription."""
    result = processor.cancel_subscription(subscription_id, immediate)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.post("/api/v1/payment-intents")
async def create_payment_intent(payment: PaymentIntentCreate):
    """Create one-time payment."""
    result = processor.create_payment_intent(
        amount=payment.amount,
        currency=payment.currency,
        customer_id=payment.customer_id
    )
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.post("/api/v1/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """Handle Stripe webhooks."""
    payload = await request.body()
    
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    event = processor.verify_webhook(payload, stripe_signature)
    
    if not event:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    result = processor.handle_webhook_event(event)
    return result

@app.get("/api/v1/customers/{customer_id}/subscriptions")
async def get_customer_subscriptions(customer_id: str):
    """Get customer subscriptions."""
    subscriptions = processor.get_customer_subscriptions(customer_id)
    return {"subscriptions": subscriptions}

@app.post("/api/v1/customers/{customer_id}/portal")
async def create_portal_session(customer_id: str, return_url: str):
    """Create customer portal session."""
    result = processor.create_portal_session(customer_id, return_url)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "payment-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
