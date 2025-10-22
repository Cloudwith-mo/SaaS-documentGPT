# 🧪 Test Your Stripe Integration

## ✅ Everything is Set Up!

- ✅ Stripe keys stored in AWS Secrets Manager
- ✅ Price IDs configured in Lambda
- ✅ Test tier ($0.09) added to pricing modal
- ✅ Frontend wired to Stripe checkout
- ✅ Lambda deployed

---

## 🚀 Test Now (5 Steps):

### 1. Open Your App
Go to: **https://documentgpt.io/backup.html**

### 2. Login/Signup
- Create a test account or login
- (Guest mode won't work for checkout)

### 3. Click "Upgrade" Button
- Should see 3 pricing tiers:
  - **Test**: $0.09/mo
  - **Monthly**: $14.99/mo  
  - **Annual**: $5.99/mo ($71.95/year)

### 4. Click "Test Checkout"
- Should redirect to Stripe Checkout page
- Use test card: **4242 4242 4242 4242**
- Expiry: **12/25**
- CVC: **123**
- ZIP: **12345**

### 5. Complete Payment
- Should redirect back to your app with `?success=true`
- Check DynamoDB for subscription entry

---

## 🔍 Verify Subscription

### Check DynamoDB:
```bash
aws dynamodb scan \
    --table-name documentgpt-subscriptions \
    --region us-east-1
```

### Check Stripe Dashboard:
1. Go to: https://dashboard.stripe.com/test/subscriptions
2. Should see your test subscription

---

## 🧹 After Testing

Once you confirm Stripe works, **delete the test tier**:

1. Go to Stripe Dashboard → Products
2. Archive the "DocumentGPT Test" product
3. Remove test tier from pricing modal in `backup.html`
4. Redeploy frontend

---

## 🐛 Troubleshooting

### "Stripe not configured" error
```bash
# Check secrets exist
aws secretsmanager get-secret-value \
    --secret-id documentgpt/stripe-secret \
    --region us-east-1
```

### Checkout doesn't redirect
- Check browser console for errors
- Verify Lambda logs in CloudWatch
- Ensure API Gateway endpoint is correct

### Subscription not in DynamoDB
- Set up webhook (see STRIPE_INTEGRATION_GUIDE.md)
- Manually trigger test webhook from Stripe Dashboard

---

## 📊 Your Stripe Configuration

**Test Mode Keys:**
- Publishable: `pk_test_51Rz1sfBgGYaywldn...`
- Secret: `sk_test_51Rz1sfBgGYaywldn...` (stored in Secrets Manager)

**Price IDs:**
- Test: `price_1S4pKeBgGYaywldnKRNWv3NE`
- Monthly: `price_1S4pOmBgGYaywldn2qTmEfbE`
- Annual: `price_1S4pQoBgGYaywldnBwoCHhaA`

**API Endpoint:**
- `/subscription` with `action: 'create'`

---

## ✨ Next Steps

1. ✅ Test checkout flow
2. ✅ Verify subscription in DynamoDB
3. ✅ Set up webhooks (optional but recommended)
4. ✅ Remove test tier
5. ✅ Switch to live mode when ready

**Test it now!** 🎉
