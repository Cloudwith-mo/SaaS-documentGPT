# Complete Stripe Integration Guide for DocumentGPT

## Step 1: Create Stripe Account & Products

### 1.1 Sign up for Stripe
1. Go to https://stripe.com
2. Click "Start now" and create account
3. Complete business verification

### 1.2 Create Products in Stripe Dashboard

**Go to: Products → Add Product**

#### Product 1: Monthly Plan
- **Name**: DocumentGPT Premium Monthly
- **Description**: Unlimited chats, documents, and AI agents
- **Pricing**: 
  - Price: $14.99
  - Billing period: Monthly
  - Currency: USD
- Click "Add product"
- **Copy the Price ID** (looks like `price_1ABC123xyz...`)

#### Product 2: Annual Plan
- **Name**: DocumentGPT Premium Annual
- **Description**: Unlimited chats, documents, and AI agents (60% off)
- **Pricing**:
  - Price: $71.95
  - Billing period: Yearly
  - Currency: USD
- Click "Add product"
- **Copy the Price ID** (looks like `price_1DEF456xyz...`)

---

## Step 2: Get Your Stripe API Keys

### 2.1 Test Mode Keys (for development)
1. Go to: Developers → API keys
2. Make sure "Test mode" toggle is ON (top right)
3. Copy:
   - **Publishable key** (starts with `pk_test_...`)
   - **Secret key** (starts with `sk_test_...`) - Click "Reveal test key"

### 2.2 Live Mode Keys (for production)
1. Toggle to "Live mode"
2. Copy:
   - **Publishable key** (starts with `pk_live_...`)
   - **Secret key** (starts with `sk_live_...`)

---

## Step 3: Store Keys in AWS Secrets Manager

```bash
# Store Stripe Secret Key (use test key first)
aws secretsmanager create-secret \
    --name documentgpt/stripe-secret \
    --secret-string "sk_test_YOUR_SECRET_KEY_HERE" \
    --region us-east-1

# Store Stripe Publishable Key
aws secretsmanager create-secret \
    --name documentgpt/stripe-publishable \
    --secret-string "pk_test_YOUR_PUBLISHABLE_KEY_HERE" \
    --region us-east-1
```

**To update existing secrets:**
```bash
aws secretsmanager update-secret \
    --secret-id documentgpt/stripe-secret \
    --secret-string "sk_test_YOUR_NEW_KEY" \
    --region us-east-1
```

---

## Step 4: Update Lambda Environment Variables

### 4.1 Via AWS Console
1. Go to Lambda → Functions → `docgpt-chat`
2. Configuration → Environment variables → Edit
3. Add:
   - Key: `STRIPE_MONTHLY_PRICE_ID`, Value: `price_1ABC123xyz...`
   - Key: `STRIPE_ANNUAL_PRICE_ID`, Value: `price_1DEF456xyz...`
4. Save

### 4.2 Via AWS CLI
```bash
aws lambda update-function-configuration \
    --function-name docgpt-chat \
    --environment "Variables={
        OPENAI_API_KEY=your_openai_key,
        STRIPE_MONTHLY_PRICE_ID=price_1ABC123xyz,
        STRIPE_ANNUAL_PRICE_ID=price_1DEF456xyz
    }" \
    --region us-east-1
```

---

## Step 5: Update Frontend to Call Stripe Checkout

Add this JavaScript to your `backup.html`:

```javascript
// Add to selectPlan function (around line 2800)
async function selectPlan(plan) {
    if (!state.user || state.user.isGuest) {
        hideModal('upgradeModal');
        showModal('loginModal');
        toast('Please login first');
        return;
    }
    
    toast('Redirecting to checkout...');
    
    try {
        // Call your Lambda to create Stripe checkout session
        const res = await fetch(`${API}/subscription`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                action: 'create',
                user_id: state.user.sub,
                plan: plan  // 'monthly' or 'annual'
            })
        });
        
        const data = await res.json();
        
        if (data.checkout_url) {
            // Redirect to Stripe Checkout
            window.location.href = data.checkout_url;
        } else {
            toast('Checkout failed: ' + (data.error || 'Unknown error'));
        }
    } catch (e) {
        toast('Error: ' + e.message);
    }
}
```

---

## Step 6: Set Up Stripe Webhooks

### 6.1 Create Webhook Endpoint
1. Go to: Developers → Webhooks → Add endpoint
2. **Endpoint URL**: `https://i1dy8i3692.execute-api.us-east-1.amazonaws.com/prod/webhook`
3. **Events to send**:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Click "Add endpoint"
5. **Copy the Signing Secret** (starts with `whsec_...`)

### 6.2 Store Webhook Secret
```bash
aws secretsmanager create-secret \
    --name documentgpt/stripe-webhook-secret \
    --secret-string "whsec_YOUR_WEBHOOK_SECRET" \
    --region us-east-1
```

---

## Step 7: Test the Integration

### 7.1 Test with Stripe Test Cards
Use these test cards in Stripe Checkout:

**Successful Payment:**
- Card: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., 12/25)
- CVC: Any 3 digits (e.g., 123)
- ZIP: Any 5 digits (e.g., 12345)

**Payment Declined:**
- Card: `4000 0000 0000 0002`

**Requires Authentication (3D Secure):**
- Card: `4000 0025 0000 3155`

### 7.2 Test Flow
1. Open https://documentgpt.io/backup.html
2. Click "Upgrade" button
3. Select "Monthly" or "Annual" plan
4. Should redirect to Stripe Checkout
5. Use test card `4242 4242 4242 4242`
6. Complete checkout
7. Should redirect back to your app with `?success=true`
8. Check DynamoDB `documentgpt-subscriptions` table for new entry

---

## Step 8: Verify Subscription Status

### 8.1 Check DynamoDB
```bash
aws dynamodb scan \
    --table-name documentgpt-subscriptions \
    --region us-east-1
```

### 8.2 Check in App
Add this to your frontend to display subscription status:

```javascript
async function loadSubscriptionStatus() {
    if (!state.user || state.user.isGuest) return;
    
    try {
        const res = await fetch(`${API}/subscription`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                action: 'status',
                user_id: state.user.sub
            })
        });
        
        const data = await res.json();
        console.log('Subscription:', data);
        
        if (data.plan === 'premium') {
            // User has active subscription
            document.getElementById('upgradeBtn').style.display = 'none';
        }
    } catch (e) {
        console.error('Failed to load subscription:', e);
    }
}

// Call after login
await initAuth();
await loadSubscriptionStatus();
```

---

## Step 9: Handle Success/Cancel Redirects

Add this to your frontend (in `DOMContentLoaded`):

```javascript
// Check for Stripe redirect
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('success') === 'true') {
    toast('🎉 Subscription activated! Welcome to Premium!', true);
    // Reload subscription status
    await loadSubscriptionStatus();
    // Clean URL
    window.history.replaceState({}, '', '/backup.html');
}
if (urlParams.get('canceled') === 'true') {
    toast('Checkout canceled. You can upgrade anytime!');
    window.history.replaceState({}, '', '/backup.html');
}
```

---

## Step 10: Go Live (Production)

### 10.1 Switch to Live Mode
1. In Stripe Dashboard, toggle to "Live mode"
2. Get your **live** API keys
3. Update AWS Secrets Manager with live keys:

```bash
aws secretsmanager update-secret \
    --secret-id documentgpt/stripe-secret \
    --secret-string "sk_live_YOUR_LIVE_SECRET_KEY" \
    --region us-east-1

aws secretsmanager update-secret \
    --secret-id documentgpt/stripe-publishable \
    --secret-string "pk_live_YOUR_LIVE_PUBLISHABLE_KEY" \
    --region us-east-1
```

4. Update Lambda environment variables with **live** Price IDs
5. Update webhook endpoint to use live mode

### 10.2 Activate Your Stripe Account
1. Complete business verification
2. Add bank account for payouts
3. Set up tax settings
4. Review and accept Stripe's terms

---

## Troubleshooting

### Issue: "Stripe not configured" error
**Solution**: Check that Secrets Manager has the correct keys:
```bash
aws secretsmanager get-secret-value \
    --secret-id documentgpt/stripe-secret \
    --region us-east-1
```

### Issue: Webhook not receiving events
**Solution**: 
1. Check webhook URL is correct
2. Verify Lambda has public API Gateway endpoint
3. Check CloudWatch logs for errors
4. Test webhook in Stripe Dashboard → Webhooks → Send test webhook

### Issue: Checkout session creation fails
**Solution**:
1. Verify Price IDs are correct
2. Check Lambda environment variables
3. Ensure Stripe secret key is valid
4. Check Lambda CloudWatch logs

### Issue: Subscription not showing in DynamoDB
**Solution**:
1. Check webhook is configured correctly
2. Verify `checkout.session.completed` event is enabled
3. Check Lambda logs for webhook processing errors
4. Manually trigger test webhook from Stripe Dashboard

---

## Quick Reference

### API Endpoints
- Create checkout: `POST /subscription` with `action: 'create'`
- Get status: `POST /subscription` with `action: 'status'`
- Cancel: `POST /subscription` with `action: 'cancel'`
- Webhook: `POST /webhook`

### DynamoDB Tables
- `documentgpt-subscriptions`: User subscription data
- `documentgpt-usage`: Usage tracking

### Environment Variables
- `STRIPE_MONTHLY_PRICE_ID`: Monthly plan price ID
- `STRIPE_ANNUAL_PRICE_ID`: Annual plan price ID

### Secrets Manager
- `documentgpt/stripe-secret`: Stripe secret key
- `documentgpt/stripe-publishable`: Stripe publishable key
- `documentgpt/stripe-webhook-secret`: Webhook signing secret

---

## Next Steps

1. ✅ Create Stripe products
2. ✅ Get API keys
3. ✅ Store in AWS Secrets Manager
4. ✅ Update Lambda environment variables
5. ✅ Test with test cards
6. ✅ Set up webhooks
7. ✅ Verify subscription flow
8. ✅ Go live with real keys

**Need help?** Check Stripe docs: https://stripe.com/docs/billing/subscriptions/overview
