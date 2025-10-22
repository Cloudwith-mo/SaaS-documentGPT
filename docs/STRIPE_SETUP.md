# Stripe Integration Setup

## 1. Create Stripe Products & Prices

Go to Stripe Dashboard → Products → Create Product

### Product 1: DocumentGPT Premium Monthly
- Name: DocumentGPT Premium Monthly
- Price: $14.99/month
- Billing: Recurring monthly
- Copy the Price ID: `price_xxxxx` (you'll need this)

### Product 2: DocumentGPT Premium Annual
- Name: DocumentGPT Premium Annual  
- Price: $71.95/year ($5.99/month - 60% off)
- Billing: Recurring yearly
- Copy the Price ID: `price_yyyyy` (you'll need this)

## 2. Store Stripe Keys in AWS Secrets Manager

```bash
# Store Stripe Secret Key
aws secretsmanager create-secret \
    --name documentgpt/stripe-secret \
    --secret-string "sk_live_YOUR_SECRET_KEY" \
    --region us-east-1

# Store Stripe Publishable Key (for frontend)
aws secretsmanager create-secret \
    --name documentgpt/stripe-publishable \
    --secret-string "pk_live_YOUR_PUBLISHABLE_KEY" \
    --region us-east-1
```

## 3. Update Lambda Environment Variables

Add these to your Lambda function:
- `STRIPE_MONTHLY_PRICE_ID`: price_xxxxx
- `STRIPE_ANNUAL_PRICE_ID`: price_yyyyy

## 4. Deploy Updated Code

```bash
# Deploy Lambda
cd lambda
zip -r function.zip simple_handler.py
aws lambda update-function-code \
    --function-name docgpt-chat \
    --zip-file fileb://function.zip

# Deploy Frontend
aws s3 cp ../web/backup.html s3://documentgpt-website-prod/backup.html
```

## 5. Test Stripe Integration

### Quick Test (Success):
1. Go to https://documentgpt.io/backup.html
2. Click "⚡ Upgrade" button in sidebar
3. Choose "Get Monthly" or "Get Annual"
4. Enter test card details:
   - **Card**: `4242 4242 4242 4242`
   - **Expiry**: Any future date (e.g., `12/25`)
   - **CVC**: Any 3 digits (e.g., `123`)
   - **ZIP**: Any 5 digits (e.g., `12345`)
5. Click "Subscribe"
6. You'll be redirected back with "✅ Welcome to Premium!" modal

### Test Different Scenarios:

**Successful Payment:**
- `4242 4242 4242 4242` - Visa (always succeeds)
- `5555 5555 5555 4444` - Mastercard (always succeeds)
- `3782 822463 10005` - American Express (always succeeds)

**Declined Payment:**
- `4000 0000 0000 0002` - Card declined
- `4000 0000 0000 9995` - Insufficient funds

**Authentication Required (3D Secure):**
- `4000 0025 0000 3155` - Requires authentication
- Complete authentication in test popup

**Test Both Plans:**
1. **Monthly Plan ($14.99/mo)**:
   - Click "Get Monthly"
   - Use `4242 4242 4242 4242`
   - Verify success modal appears
   - Check Settings → should show "Plan: Premium"

2. **Annual Plan ($71.95/yr)**:
   - Click "Get Annual"
   - Use `4242 4242 4242 4242`
   - Verify success modal appears
   - Check Settings → should show "Plan: Premium"

### Verify Subscription:
1. After successful payment, go to Settings (⚙️)
2. Should see "Subscription" section with:
   - "Plan: Premium"
   - "Cancel Subscription" button
3. Try unlimited chats (no limit warnings)

### Test Cancellation:
1. Go to Settings (⚙️)
2. Click "Cancel Subscription"
3. Confirm cancellation
4. Should see "✅ Subscription canceled" toast
5. Check Stripe Dashboard → subscription should be canceled

## 6. View Test Payments in Stripe

1. Go to Stripe Dashboard → Payments
2. Toggle "Viewing test data" (top right)
3. See all test payments and subscriptions
4. Click any payment to see details

## 7. Webhook Setup (Optional but Recommended)

Create webhook endpoint in Stripe Dashboard:
- URL: https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod/webhook
- Events: `customer.subscription.created`, `customer.subscription.deleted`, `invoice.payment_succeeded`

## Price IDs to Update

Replace these in the code:
- `MONTHLY_PRICE_ID` = your monthly price ID
- `ANNUAL_PRICE_ID` = your annual price ID
