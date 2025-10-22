# Rate Limiting & Paywall Implementation

## Overview
Implemented hard rate limits with graceful paywall modal for free tier users.

## Free Tier Limits
- **Chats**: 10 per month
- **Documents**: 2 total
- **Agents**: 0 (premium only)

## Implementation

### Backend (Lambda)
**File**: `lambda/simple_handler.py`

1. **Rate Limit Check**:
   - Returns `402 Payment Required` when free user exceeds limit
   - Includes usage data in response: `{used: X, limit: Y, message: "..."}`

2. **Event Tracking**:
   - New `track_event()` function logs "upgrade_shown" events
   - Stores events in `documentgpt-usage` table
   - Keeps last 100 events per user for analytics

3. **Usage Functions**:
   - `check_usage_limit()`: Returns true/false if user can proceed
   - `get_current_usage()`: Returns current usage count
   - `track_event()`: Logs analytics events

### Frontend (backup.html)
**File**: `web/backup.html`

1. **Preemptive Check**:
   - Checks usage before API call
   - Shows paywall modal immediately if at limit
   - Prevents unnecessary API requests

2. **Paywall Modal**:
   - Beautiful gradient design with rocket emoji 🚀
   - Shows current usage: "X / Y chats used"
   - Lists Premium benefits
   - Two CTAs: "Maybe Later" and "Upgrade Now"
   - Tracks `paywall_shown` event in PostHog/GA

3. **402 Response Handling**:
   - Catches 402 status from API
   - Displays paywall modal with server data
   - Rolls back optimistic usage update

## User Experience

### Free User Flow
1. User sends 10th chat → Success
2. User tries 11th chat → Preemptive check shows paywall
3. User clicks "Upgrade Now" → Opens upgrade modal
4. User selects plan → Redirects to Stripe
5. After payment → Unlimited access

### Premium User Flow
1. No limits enforced
2. Backend checks subscription status
3. Returns unlimited access

## Analytics Events

### Tracked Events
- `upgrade_shown`: When paywall is displayed
  - Metadata: `{reason: 'chat_limit', used: X, limit: Y}`
- `paywall_shown`: PostHog/GA tracking
  - Properties: `{reason: 'chat_limit', used: X, limit: Y}`

### Conversion Funnel
1. Free user hits limit
2. Paywall shown (tracked)
3. User clicks "Upgrade Now"
4. User completes payment
5. Subscription activated

## Testing

### Test Free Tier Limit
1. Create new account or use guest mode
2. Send 10 chats
3. Try 11th chat → Should see paywall modal
4. Click "Upgrade Now" → Should open upgrade modal

### Test Premium Bypass
1. Login with premium account
2. Send unlimited chats
3. No paywall should appear

## Configuration

### Adjust Limits
Edit `CONFIG` in `backup.html`:
```javascript
const CONFIG = {
    CHAT_LIMIT: 10,  // Free tier chat limit
    DOC_LIMIT: 2     // Free tier document limit
};
```

Edit limits in `simple_handler.py`:
```python
limits = {'chat': 10, 'document': 2, 'agent': 0}
```

## Deployment Status
✅ Lambda deployed: 2025-10-19T00:55:19.000+0000
✅ Frontend deployed: backup.html (227.1 KiB)

## Next Steps
1. Monitor conversion rate (paywall_shown → subscription)
2. A/B test paywall messaging
3. Add "1 free chat per day" for engaged free users
4. Implement email reminder when approaching limit
