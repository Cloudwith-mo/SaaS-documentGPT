# DocumentGPT Environments

## 🌍 4-Environment Structure

### 1. **DEV** - Daily Development
- **URL**: https://documentgpt.io/backup-unified.html
- **Purpose**: Active development, daily iterations
- **Update Frequency**: Multiple times per day
- **Stability**: Unstable, breaking changes expected

### 2. **STG** - Original Staging
- **URL**: https://documentgpt.io/backup.html
- **Purpose**: Stable baseline without gamification
- **Update Frequency**: As needed for core fixes
- **Stability**: Stable

### 3. **STG-V2** - Approved Features Staging
- **URL**: https://documentgpt.io/staging-v2.html
- **Purpose**: Approved features from DEV before production
- **Update Frequency**: After approval from DEV
- **Stability**: Very stable, production-ready

### 4. **PRD** - Production
- **URL**: https://documentgpt.io/ (index.html)
- **Purpose**: Public-facing stable release
- **Update Frequency**: Monthly or when major features ready
- **Stability**: Rock solid

---

## 🚀 Deployment Workflow

```
DEV (backup-unified.html)
    ↓ (test & get approval)
    ↓
STG-V2 (staging-v2.html)
    ↓ (final testing & approval)
    ↓
PRD (index.html)
```

---

## 📝 Deployment Commands

### Deploy to DEV
```bash
aws s3 cp web/backup-unified.html s3://documentgpt-website-prod/backup-unified.html --content-type "text/html"
```

### Deploy to STG-V2 (after approval)
```bash
aws s3 cp web/backup-unified.html s3://documentgpt-website-prod/staging-v2.html --content-type "text/html"
```

### Deploy to PRD (after final approval)
```bash
aws s3 cp s3://documentgpt-website-prod/staging-v2.html web/index.html
aws s3 cp web/index.html s3://documentgpt-website-prod/index.html --content-type "text/html"
```

---

## 📊 Current Status

✅ **STG-V2 created** - Cloned from STG (backup.html)
✅ **Ready for approved features** from DEV
