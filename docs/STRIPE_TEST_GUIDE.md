# Stripe Test Card Guide

## 🚀 Quick Test (2 minutes)

### Test Monthly Plan:
1. Open https://documentgpt.io/backup.html
2. Click "⚡ Upgrade" in sidebar
3. Click "Get Monthly" ($14.99/month)
4. Enter:
   - Card: `4242 4242 4242 4242`
   - Expiry: `12/25`
   - CVC: `123`
   - ZIP: `12345`
5. Click "Subscribe"
6. ✅ See "Welcome to Premium!" modal

### Test Annual Plan:
1. Same steps but click "Get Annual" ($71.95/year)
2. Use same test card
3. ✅ See success modal

### Test Cancel:
1. Click Settings (⚙️)
2. Scroll to "Subscription" section
3. Click "Cancel Subscription"
4. Confirm
5. ✅ See "Subscription canceled" toast

---

## 💳 Stripe Test Cards

### Always Succeeds:
- `4242 4242 4242 4242` - Visa
- `5555 5555 5555 4444` - Mastercard
- `3782 822463 10005` - Amex

### Always Fails:
- `4000 0000 0000 0002` - Card declined
- `4000 0000 0000 9995` - Insufficient funds
- `4000 0000 0000 0069` - Expired card

### Requires 3D Secure:
- `4000 0025 0000 3155` - Authentication required

**For all cards:**
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

---

## ✅ What to Verify

### After Successful Payment:
- [ ] Redirected to `?success=true`
- [ ] "✅ Welcome to Premium!" modal appears
- [ ] Settings shows "Plan: Premium"
- [ ] "Cancel Subscription" button visible
- [ ] No chat/document limits

### In Stripe Dashboard:
1. Go to https://dashboard.stripe.com/test/payments
2. Toggle "Viewing test data" (top right)
3. See your test payment
4. Click payment → see customer details

### After Cancellation:
- [ ] "✅ Subscription canceled" toast
- [ ] Settings updated
- [ ] Stripe shows subscription canceled

---

## 🐛 Troubleshooting

**"Checkout failed" error:**
- Check Lambda environment variables have correct Price IDs
- Verify Stripe secret key in AWS Secrets Manager

**Success modal doesn't appear:**
- Check browser console for errors
- Verify URL has `?success=true` parameter

**Cancel button not showing:**
- Must be logged in (not guest)
- Must have active subscription

---

## 📊 Test Checklist

- [ ] Monthly plan checkout works
- [ ] Annual plan checkout works
- [ ] Success modal appears
- [ ] Premium features unlocked
- [ ] Cancel subscription works
- [ ] Stripe dashboard shows payments
- [ ] Both test cards work (Visa + Mastercard)
- [ ] Declined card shows error
