# Deployment Guide

## Quick Deploy

```bash
./deploy.sh
```

This will:
1. ✅ Auto-commit any changes (prompts for message)
2. ✅ Deploy to chosen environment
3. ✅ Prompt for manual test
4. ✅ Tag successful deployments

## Manual Test Checklist

After each deploy, test:

1. **Upload**: Upload a PDF document
2. **Chat**: Ask "What are the key points?"
3. **Verify**: AI responds with document summary

If test fails, rollback:
```bash
git revert HEAD
./deploy.sh
```

## Environments

| Environment | URL | Use Case |
|------------|-----|----------|
| Dev | https://documentgpt.io/backup.html | Daily development |
| Staging | https://documentgpt.io/staging-v2.html | Pre-production testing |
| Production | https://documentgpt.io/app.html | Live users |

## CloudWatch Alarms

### Setup (One-time)

```bash
./setup-alarms.sh
```

Enter your email and confirm the subscription.

### What You'll Get Alerted For

- **Lambda Errors**: 5+ errors in 5 minutes
- **Lambda Throttles**: Any throttling detected
- **Slow Responses**: >10s average response time

### View Alarms

https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:

## Deployment Workflow

### Daily Development
```bash
# Make changes to web/backup.html
./deploy.sh
# Choose: 1) Dev
# Test at backup.html
```

### Pre-Production
```bash
# When ready for testing
./deploy.sh
# Choose: 2) Staging
# Test at staging-v2.html
```

### Production Release
```bash
# When staging tests pass
./deploy.sh
# Choose: 3) Production
# Test at app.html
# Monitor CloudWatch for 10 minutes
```

## Rollback

If production breaks:

```bash
# Revert last commit
git revert HEAD

# Redeploy
./deploy.sh
# Choose: 3) Production
```

## Git Tags

Successful deployments are auto-tagged:
```bash
# View deployment history
git tag -l "deploy-*"

# Rollback to specific deployment
git checkout deploy-20241019-143022
./deploy.sh
```

## Monitoring

### Check Lambda Health
```bash
aws logs tail /aws/lambda/docgpt-chat --since 10m --region us-east-1
```

### Check Recent Errors
```bash
aws logs tail /aws/lambda/docgpt-chat --since 1h --region us-east-1 | grep ERROR
```

### Check API Gateway Metrics
https://console.aws.amazon.com/apigateway/home?region=us-east-1#/apis/i1dy8i3692/stages/prod

## Cost Monitoring

Current setup: $8-15/month

- Lambda: ~$5/month
- DynamoDB: ~$2/month
- API Gateway: ~$1/month
- S3: <$1/month
- CloudWatch: <$1/month

## Emergency Contacts

- **AWS Support**: https://console.aws.amazon.com/support/
- **Stripe Support**: https://dashboard.stripe.com/support
- **OpenAI Status**: https://status.openai.com/

## Best Practices

1. **Always test in dev first**
2. **Deploy to staging before production**
3. **Monitor CloudWatch for 10 minutes after production deploy**
4. **Keep git commits small and descriptive**
5. **Tag successful production deploys**

---

**Last Updated**: October 19, 2024
