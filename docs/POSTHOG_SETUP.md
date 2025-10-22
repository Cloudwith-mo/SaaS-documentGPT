# PostHog Analytics Setup

## Current Status

✅ PostHog snippet already installed
⚠️ Using test key: `phc_test_key`

## Setup (5 minutes)

### 1. Get Your PostHog Key

1. Go to https://app.posthog.com/signup (or login)
2. Create a project (or use existing)
3. Go to Project Settings → Project API Key
4. Copy your key (starts with `phc_`)

### 2. Replace Test Key

Edit `web/backup.html` line 41:

```javascript
// BEFORE
posthog.init('phc_test_key',{api_host:'https://app.posthog.com'});

// AFTER
posthog.init('phc_YOUR_REAL_KEY',{api_host:'https://app.posthog.com'});
```

### 3. Deploy

```bash
./deploy.sh
# Choose: 4) All environments
```

## Events Already Tracked ✅

### Critical Funnel Events

1. **signup** - User creates account
   - Properties: `email`
   - Location: Line 2388

2. **upload_doc** - User uploads document
   - Properties: `file_type`
   - Location: Line 1954

3. **chat_sent** - User sends chat message
   - Location: Line 2071 (via gtag)

4. **upgrade** - User clicks upgrade button
   - Properties: `plan`
   - Location: Line 3862

5. **subscription_success** - Payment completed
   - Location: Line 4223

### Additional Events

- `export` - Document export (line 2177)
- `paywall_shown` - Free tier limit hit (line 4191)
- `autocomplete_accepted` - AI suggestion accepted (line 2852)
- `library_opened` - User opens document library (line 3934)

## PostHog Dashboard

### Key Funnels to Track

**Signup Funnel**:
```
visit → signup → upload_doc → chat_sent
```

**Conversion Funnel**:
```
upload_doc → paywall_shown → upgrade → subscription_success
```

**Engagement Funnel**:
```
signup → upload_doc → chat_sent (3+ times) → export
```

### Metrics to Monitor

1. **Signup Rate**: visits → signups
2. **Activation Rate**: signups → upload_doc
3. **Engagement Rate**: upload_doc → chat_sent (3+)
4. **Conversion Rate**: paywall_shown → subscription_success
5. **Time to First Upload**: signup → upload_doc

## View Your Data

1. **Events**: https://app.posthog.com/events
2. **Funnels**: https://app.posthog.com/insights?insight=FUNNELS
3. **Dashboards**: https://app.posthog.com/dashboard

## UTM Tracking

PostHog automatically captures UTM parameters:
- `utm_source`
- `utm_medium`
- `utm_campaign`

Example URL:
```
https://documentgpt.io/?utm_source=twitter&utm_medium=social&utm_campaign=launch
```

View by UTM: Insights → Filter by UTM parameters

## Free Tier Limits

- **1M events/month** (plenty for 0-10K users)
- **1 year data retention**
- **Unlimited team members**

## Cost at Scale

- 0-1M events: **Free**
- 1M-10M events: **$0.00031/event** (~$3/month at 10K events)
- 10M+ events: Volume discounts

## Privacy & GDPR

PostHog is GDPR compliant. To respect user privacy:

1. Add cookie banner (optional for now)
2. Anonymize IPs (already enabled by default)
3. Don't track PII in custom properties

## Testing

After deploying with real key:

1. Open https://documentgpt.io/backup.html
2. Sign up with test email
3. Upload a document
4. Send a chat
5. Check PostHog Events page (data appears in ~30 seconds)

## Troubleshooting

**Events not showing?**
- Check browser console for PostHog errors
- Verify key is correct (starts with `phc_`)
- Check ad blockers aren't blocking PostHog

**Duplicate events?**
- Normal during development (multiple page loads)
- Production will show accurate counts

---

**Last Updated**: October 19, 2024
