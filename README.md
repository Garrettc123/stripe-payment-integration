# Stripe Payment Integration

🚀 Production-grade payment processing with Stripe subscriptions, webhooks, and customer management.

## Features

✅ **Subscription Management**
- Multiple pricing tiers (Starter, Pro, Enterprise)
- Trial periods
- Upgrade/downgrade with proration
- Cancellation handling

✅ **Payment Processing**
- One-time payments
- Recurring billing
- Automatic retries
- Customer portal

✅ **Webhooks**
- Secure signature verification
- Event handling for all payment events
- Automatic service provisioning/deprovisioning

✅ **Security**
- Webhook signature verification
- Environment variable configuration
- No hardcoded secrets

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Stripe keys
```

### 3. Run API Server

```bash
python src/api.py
```

API runs on `http://localhost:8000`

### 4. Test Webhook Locally

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
```

## API Endpoints

### Create Customer
```bash
POST /api/v1/customers
{
  "email": "customer@example.com",
  "name": "John Doe"
}
```

### Create Subscription
```bash
POST /api/v1/subscriptions
{
  "customer_id": "cus_xxx",
  "tier": "pro",
  "trial_days": 14
}
```

### Cancel Subscription
```bash
DELETE /api/v1/subscriptions/{subscription_id}?immediate=false
```

### Create Payment Intent
```bash
POST /api/v1/payment-intents
{
  "amount": 4900,
  "currency": "usd",
  "customer_id": "cus_xxx"
}
```

## Pricing Tiers

| Tier | Price | Features |
|------|-------|----------|
| **Starter** | $49/mo | 10GB data, 5 pipelines, Email support |
| **Pro** | $199/mo | 100GB data, Unlimited pipelines, Priority support |
| **Enterprise** | $499/mo | Unlimited data, Custom integrations, Dedicated support |

## Deployment

### Docker

```bash
docker build -t payment-api .
docker run -p 8000:8000 --env-file .env payment-api
```

### Railway/Render

1. Connect GitHub repo
2. Add environment variables
3. Deploy

## Webhook Events Handled

- `payment_intent.succeeded` - Activate service
- `payment_intent.payment_failed` - Suspend service
- `customer.subscription.created` - Provision resources
- `customer.subscription.updated` - Update resources
- `customer.subscription.deleted` - Deprovision resources
- `invoice.payment_succeeded` - Extend subscription
- `invoice.payment_failed` - Send payment failure notification

## Security Best Practices

✅ Webhook signature verification  
✅ Environment variable secrets  
✅ No API keys in code  
✅ HTTPS only in production  
✅ Rate limiting (recommended)  

## Testing

Use Stripe test cards:
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- 3D Secure: `4000 0025 0000 3155`

## Production Checklist

- [ ] Replace test keys with live keys
- [ ] Configure production webhook endpoint
- [ ] Enable Stripe Radar for fraud detection
- [ ] Set up monitoring/alerts
- [ ] Implement rate limiting
- [ ] Add database for customer records
- [ ] Configure backup payment methods
- [ ] Test subscription lifecycle

## License

MIT
