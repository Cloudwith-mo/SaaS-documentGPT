# Gaps Analysis - DocumentGPT

## ✅ Working Features (Verified)

1. **Chat** - ✅ 200 OK, AI responses, usage tracked
2. **Document Upload** - ✅ 200 OK, saved to DynamoDB, smart questions generated
3. **Summary Agent** - ✅ 200 OK, AI summaries
4. **Export Agent** - ✅ 200 OK, S3 upload, download URL
5. **Calendar Agent** - ✅ 200 OK, iCal generation
6. **Save Agent** - ✅ 200 OK, DynamoDB persistence
7. **Usage Tracking** - ✅ Increments correctly (chats, docs, agents)
8. **Testing Tier** - ✅ Unlimited access for development

## ❌ Gaps Identified

### 1. Email Agent - SES Verification (CRITICAL)
**Status**: Returns error "MessageRejected"
**Issue**: `noreply@documentgpt.io` not verified in SES
**Fix**: 
```bash
aws sesv2 create-email-identity --email-identity noreply@documentgpt.io --region us-east-1
# Click verification link in email
```
**Priority**: HIGH (blocks email functionality)

### 2. Usage Endpoint - CORS/Auth Issue
**Status**: Returns 403 Forbidden
**Issue**: GET /usage endpoint not handling CORS or missing auth
**Fix**: Add proper CORS headers and auth handling
**Priority**: MEDIUM (frontend can't display usage stats)

### 3. Sheets/CSV Agent - Not Tested
**Status**: Unknown (code exists but not tested)
**Issue**: Need to verify CSV export works
**Fix**: Test with actual CSV data
**Priority**: LOW (code identical to export agent)

### 4. Frontend Integration Gaps

#### A. PDF Upload/Rendering
**Status**: Not implemented
**Issue**: App can't handle PDF files (only text)
**Fix**: 
- Add PDF.js library
- Extract text from PDF
- Display PDF in viewer
**Priority**: HIGH (user requested PDF testing)

#### B. Document Download
**Status**: Not implemented
**Issue**: No way to download uploaded documents
**Fix**: Add download button that fetches from S3/DynamoDB
**Priority**: MEDIUM

#### C. Error Handling
**Status**: Minimal
**Issue**: 403 errors not shown to user with upgrade prompt
**Fix**: Add error modals with clear messaging
**Priority**: MEDIUM

#### D. Usage Display
**Status**: Not working
**Issue**: Can't fetch usage stats due to 403
**Fix**: Fix backend CORS, then wire to UI
**Priority**: MEDIUM

### 5. Missing Backend Features

#### A. Document Listing
**Status**: Not implemented
**Issue**: No endpoint to list user's documents
**Fix**: Add GET /documents endpoint with DynamoDB query
**Priority**: HIGH (needed for document management)

#### B. Document Deletion
**Status**: Not implemented
**Issue**: No way to delete documents
**Fix**: Add DELETE /documents/{doc_id} endpoint
**Priority**: MEDIUM

#### C. Folder Organization
**Status**: Not implemented
**Issue**: All docs in flat structure
**Fix**: Add folder schema to DynamoDB
**Priority**: LOW (nice-to-have)

#### D. Search Functionality
**Status**: Not implemented
**Issue**: Can't search through documents
**Fix**: Add search endpoint with DynamoDB scan/filter
**Priority**: LOW

### 6. Stripe Integration
**Status**: Not started
**Issue**: No payment processing
**Fix**: 
- Create Stripe products/prices
- Implement checkout flow
- Add webhook handler
- Wire subscription management
**Priority**: HIGH (required for monetization)

## 📊 Priority Matrix

### Must Fix Before Launch (P0)
1. ✅ Agent tracking (FIXED)
2. ❌ Email Agent SES verification
3. ❌ PDF upload/rendering
4. ❌ Document listing endpoint
5. ❌ Stripe integration

### Should Fix Soon (P1)
6. ❌ Usage endpoint CORS
7. ❌ Document download
8. ❌ Error handling UI
9. ❌ Document deletion

### Nice to Have (P2)
10. ❌ Sheets/CSV agent testing
11. ❌ Folder organization
12. ❌ Search functionality

## 🔧 Quick Fixes (< 30 min each)

### Fix 1: Usage Endpoint CORS
```python
# In simple_handler.py, line ~180
elif path == '/usage' and method == 'GET':
    user_id = event.get('queryStringParameters', {}).get('user_id')
    if not user_id:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'user_id required'})
        }
    return get_usage_stats(user_id)
```

### Fix 2: Document Listing
```python
# Add new endpoint
elif path == '/documents' and method == 'GET':
    user_id = event.get('queryStringParameters', {}).get('user_id')
    docs_table = dynamodb.Table('docgpt')
    response = docs_table.query(
        KeyConditionExpression='pk = :pk',
        ExpressionAttributeValues={':pk': f'USER#{user_id}'}
    )
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({'documents': response['Items']})
    }
```

### Fix 3: SES Email Verification
```bash
aws sesv2 create-email-identity --email-identity noreply@documentgpt.io --region us-east-1
```

## 📈 Completion Status

**Backend**: 75% complete
- ✅ Core endpoints (chat, upload, agents)
- ✅ Usage tracking
- ✅ Document persistence
- ❌ Document management (list, delete)
- ❌ SES verification
- ❌ Stripe integration

**Frontend**: 60% complete
- ✅ UI/UX design
- ✅ Chat interface
- ✅ Agent buttons
- ❌ PDF handling
- ❌ Document management
- ❌ Error handling
- ❌ Usage display

**Overall**: 68% production-ready

## 🎯 Next Steps (Recommended Order)

1. **Fix Usage Endpoint** (5 min) - Add proper CORS handling
2. **Add Document Listing** (15 min) - GET /documents endpoint
3. **Fix SES Email** (5 min) - Verify email address
4. **Add PDF Support** (60 min) - PDF.js integration + text extraction
5. **Add Document Download** (20 min) - Download button + S3 fetch
6. **Stripe Integration** (120 min) - Full payment flow
7. **Error Handling** (30 min) - User-friendly error modals
8. **Document Deletion** (15 min) - DELETE endpoint

**Total Time to MVP**: ~4.5 hours

## 🚨 Critical Path to Launch

1. Usage endpoint fix
2. Document listing
3. PDF support
4. Stripe integration

Everything else can be added post-launch.
