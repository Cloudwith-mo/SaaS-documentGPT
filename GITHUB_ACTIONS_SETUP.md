# GitHub Actions Setup Guide

**Time:** 10 minutes  
**Result:** Automated Lambda deployments on every push

---

## ✅ What Was Created

**File:** `.github/workflows/deploy-lambda.yml`

**Triggers:**
- Push to `main` branch (when `lambda/` changes)
- Manual trigger (workflow_dispatch)

**What it does:**
1. Builds Docker image on x86_64 Linux (ubuntu-latest)
2. Pushes to ECR
3. Updates Lambda function
4. Tests deployment

---

## 🔧 Setup Steps

### Step 1: Add AWS Credentials to GitHub (5 minutes)

1. **Go to GitHub repo settings:**
   ```
   https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions
   ```

2. **Click "New repository secret"**

3. **Add these secrets:**

   **Secret 1:**
   - Name: `AWS_ACCESS_KEY_ID`
   - Value: Your AWS access key

   **Secret 2:**
   - Name: `AWS_SECRET_ACCESS_KEY`
   - Value: Your AWS secret key

### Step 2: Create AWS IAM User (if needed)

If you don't have AWS credentials:

```bash
# Create IAM user
aws iam create-user --user-name github-actions-lambda

# Attach policies
aws iam attach-user-policy \
  --user-name github-actions-lambda \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

aws iam attach-user-policy \
  --user-name github-actions-lambda \
  --policy-arn arn:aws:iam::aws:policy/AWSLambda_FullAccess

# Create access key
aws iam create-access-key --user-name github-actions-lambda
```

Copy the AccessKeyId and SecretAccessKey to GitHub secrets.

### Step 3: Push to GitHub (2 minutes)

```bash
cd /Users/muhammadadeyemi/documentgpt.io/SaaS-documentGPT

git add .github/workflows/deploy-lambda.yml
git commit -m "Add GitHub Actions for Lambda deployment"
git push origin main
```

### Step 4: Watch it Deploy (3 minutes)

1. Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`
2. Click on the running workflow
3. Watch it build and deploy
4. ✅ Done!

---

## 🧪 Testing

### Manual Trigger
```
1. Go to Actions tab
2. Click "Deploy Lambda"
3. Click "Run workflow"
4. Select branch: main
5. Click "Run workflow"
```

### Automatic Trigger
```bash
# Make any change to lambda code
echo "# test" >> lambda/dev_handler.py
git add lambda/dev_handler.py
git commit -m "Test deployment"
git push
```

Workflow runs automatically!

---

## 📊 What Happens

```
┌─────────────────────────────────────────┐
│  You: git push                          │
└─────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  GitHub Actions (ubuntu-latest x86_64)  │
│                                         │
│  1. Checkout code                       │
│  2. Configure AWS                       │
│  3. Login to ECR                        │
│  4. Build Docker image ✅ Single-arch   │
│  5. Push to ECR                         │
│  6. Update Lambda                       │
│  7. Wait for update                     │
│  8. Test health endpoint                │
└─────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Lambda: Updated with new code ✅       │
└─────────────────────────────────────────┘
```

---

## 🎯 Benefits

**Before (M1/M2 Mac):**
- ❌ Docker creates multi-arch manifest
- ❌ Lambda rejects image
- ❌ Manual console edits required

**After (GitHub Actions):**
- ✅ Builds on x86_64 Linux
- ✅ Creates single-arch manifest
- ✅ Lambda accepts image
- ✅ Fully automated

---

## 🔍 Troubleshooting

### Workflow fails at "Configure AWS credentials"
**Fix:** Check GitHub secrets are set correctly

### Workflow fails at "Build and push Docker image"
**Fix:** Check Dockerfile.dev exists in lambda/

### Workflow fails at "Update Lambda function"
**Fix:** Check Lambda function name is correct

### Image still rejected by Lambda
**Fix:** This shouldn't happen on ubuntu-latest, but verify:
```bash
# In workflow, add debug step:
- name: Check manifest type
  run: |
    docker manifest inspect $IMAGE_URI | jq '.mediaType'
```

Should output: `application/vnd.docker.distribution.manifest.v2+json`

---

## 📝 Workflow File Explained

```yaml
name: Deploy Lambda  # Workflow name

on:
  push:
    branches: [main]  # Trigger on push to main
    paths:
      - 'lambda/**'   # Only when lambda/ changes
  workflow_dispatch:  # Allow manual trigger

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: documentgpt-dev-lambda
  LAMBDA_FUNCTION: documentgpt-dev-langchain

jobs:
  deploy:
    runs-on: ubuntu-latest  # ← x86_64 Linux (KEY!)
    
    steps:
      - uses: actions/checkout@v4  # Get code
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build and push Docker image
        run: |
          cd lambda
          docker build -t $IMAGE -f Dockerfile.dev .
          docker push $IMAGE
      
      - name: Update Lambda function
        run: |
          aws lambda update-function-code \
            --function-name $LAMBDA_FUNCTION \
            --image-uri $IMAGE
      
      - name: Test deployment
        run: |
          curl -f https://YOUR_LAMBDA_URL/dev/health
```

---

## ✅ Success Criteria

After setup, you should see:

1. **GitHub Actions tab:** Green checkmark ✅
2. **Lambda console:** New image deployed
3. **Test endpoint:** Returns 200 OK
4. **Manifest type:** `application/vnd.docker.distribution.manifest.v2+json`

---

## 🎉 You're Done!

**Now every push to main automatically:**
1. Builds Docker image (x86_64)
2. Pushes to ECR
3. Updates Lambda
4. Tests deployment

**No more M1/M2 issues!**  
**No more manual console edits!**  
**Fully automated deployments!**

---

## 📊 Cost

**GitHub Actions:**
- Free tier: 2,000 minutes/month
- This workflow: ~3 minutes per run
- Cost: $0 (unless you run 600+ times/month)

**Total:** FREE ✅

---

## 🚀 Next Steps

1. ✅ Set up GitHub secrets (5 min)
2. ✅ Push workflow file (1 min)
3. ✅ Watch it deploy (3 min)
4. ✅ Test endpoint (1 min)
5. 🎉 Celebrate automated deployments!

**Time to setup:** 10 minutes  
**Time saved per deployment:** 5+ minutes  
**ROI:** Infinite after 2 deployments
