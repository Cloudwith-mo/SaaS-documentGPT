import json
import urllib3
import os
import boto3
import base64
import io
from datetime import datetime, timedelta
from decimal import Decimal
from jose import jwt, JWTError
try:
    import PyPDF2
except:
    PyPDF2 = None

from config import get_settings, make_cors_headers

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)

http = urllib3.PoolManager()
settings = get_settings()
OPENAI_API_KEY = settings.openai_api_key
DOC_TABLE = settings.doc_table
dynamodb = boto3.resource('dynamodb')
secretsmanager = boto3.client('secretsmanager')
s3 = boto3.client('s3')
ses = boto3.client('ses', region_name='us-east-1')

OPENAI_API_KEY_SECRET_NAME = os.environ.get('OPENAI_API_KEY_SECRET_NAME')
if OPENAI_API_KEY_SECRET_NAME:
    try:
        OPENAI_API_KEY = secretsmanager.get_secret_value(SecretId=OPENAI_API_KEY_SECRET_NAME)['SecretString']
    except Exception as exc:
        print(f"⚠️ Failed to load OpenAI key from secret {OPENAI_API_KEY_SECRET_NAME}: {exc}")

# Get Stripe secret key
try:
    stripe_secret = secretsmanager.get_secret_value(SecretId='documentgpt/stripe-secret')['SecretString']
except:
    stripe_secret = None

# Stripe Price IDs (set these in Lambda environment variables)
STRIPE_TEST_PRICE_ID = os.environ.get('STRIPE_TEST_PRICE_ID', 'price_test')
STRIPE_MONTHLY_PRICE_ID = os.environ.get('STRIPE_MONTHLY_PRICE_ID', 'price_monthly')
STRIPE_ANNUAL_PRICE_ID = os.environ.get('STRIPE_ANNUAL_PRICE_ID', 'price_annual')

# Cognito configuration
COGNITO_REGION = 'us-east-1'
COGNITO_USER_POOL_ID = 'us-east-1_UcrfhrZOs'
COGNITO_APP_CLIENT_ID = '570a98p0qringma32hnf13olue'
COGNITO_JWKS_URL = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json'

# Cache for Cognito public keys
cognito_keys = None

def get_cognito_keys():
    """Fetch and cache Cognito public keys"""
    global cognito_keys
    if cognito_keys is None:
        response = http.request('GET', COGNITO_JWKS_URL)
        cognito_keys = json.loads(response.data.decode('utf-8'))
    return cognito_keys

def verify_token(token):
    """Verify Cognito JWT token and return user_id"""
    try:
        # Get public keys
        keys = get_cognito_keys()
        
        # Get the kid from the token header
        headers = jwt.get_unverified_headers(token)
        kid = headers['kid']
        
        # Find the correct key
        key = None
        for k in keys['keys']:
            if k['kid'] == kid:
                key = k
                break
        
        if not key:
            raise Exception('Public key not found')
        
        # Verify the token
        payload = jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}'
        )
        
        return payload['sub']  # Return user_id
    except JWTError as e:
        raise Exception(f'Token validation failed: {str(e)}')
    except Exception as e:
        raise Exception(f'Token verification error: {str(e)}')

def make_headers(request_headers=None, content_type='application/json'):
    return make_cors_headers(
        settings,
        request_headers=request_headers,
        content_type=content_type,
        allow_headers='Content-Type,Authorization,X-Requested-With',
        allow_methods='GET,POST,OPTIONS,DELETE,PUT',
        add_origin_header=True,
        vary_origin=True,
        send_wildcard_credentials=False,
    )

def lambda_handler(event, context):
    request_headers = event.get('headers') or {}
    headers = make_headers(request_headers)
    
    try:
        # Handle OPTIONS preflight immediately
        if event.get('httpMethod') == 'OPTIONS':
            return {'statusCode': 200, 'headers': headers, 'body': ''}
        
        path = event.get('path', '')
        method = event.get('httpMethod', '')
        
        # Skip auth for webhook endpoint
        if path == '/webhook':
            return handle_stripe_webhook(event)
        
        # Extract and verify token for authenticated users
        auth_header = event.get('headers', {}).get('Authorization') or event.get('headers', {}).get('authorization')
        user_id = None
        
        if auth_header:
            # Authenticated user - verify token
            token = auth_header.replace('Bearer ', '').replace('bearer ', '')
            try:
                user_id = verify_token(token)
            except Exception as e:
                return {
                    'statusCode': 401,
                    'headers': headers,
                    'body': json.dumps({'error': f'Invalid token: {str(e)}'})
                }
        else:
            # Guest user - extract guest_id from request body
            try:
                body = json.loads(event.get('body', '{}'))
                user_id = body.get('user_id')
                if not user_id or not user_id.startswith('guest_'):
                    return {
                        'statusCode': 401,
                        'headers': headers,
                        'body': json.dumps({'error': 'Missing authentication or guest_id'})
                    }
            except:
                return {
                    'statusCode': 401,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing authentication'})
                }
        
        if path == '/chat' and method == 'POST':
            body = json.loads(event['body'])
            messages = body.get('messages', [])
            # user_id comes from verified token, not request body
            
            if not messages:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'No messages provided'})
                }
            
            # Check usage limits - return 402 for free tier limit
            if user_id and not check_usage_limit(user_id, 'chat'):
                # Track upgrade_shown event
                track_event(user_id, 'upgrade_shown', {'reason': 'chat_limit'})
                return {
                    'statusCode': 402,
                    'headers': headers,
                    'body': json.dumps({
                        'error': 'Chat limit reached',
                        'message': 'You\'ve used all 10 free chats this month. Upgrade to Premium for unlimited chats!',
                        'limit': 10,
                        'used': get_current_usage(user_id, 'chat')
                    })
                }
            
            # Use gpt-4o-mini for faster responses
            question = messages[-1]['content']
            use_mini = len(question) < 500  # Use mini for short queries
            response = openai_chat(question, use_mini=use_mini)
            
            # Track usage
            if user_id:
                track_usage(user_id, 'chat')
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'response': response})
            }
        
        elif path == '/agent' and method == 'POST':
            body = json.loads(event['body'])
            agent_type = body.get('agent_type')
            content = body.get('content', '')
            # user_id comes from verified token
            params = body.get('params', {})
            
            # Check if premium agent requires subscription
            if user_id and agent_type != 'summary':
                sub_table = dynamodb.Table('documentgpt-subscriptions')
                sub_resp = sub_table.get_item(Key={'user_id': user_id})
                plan = sub_resp.get('Item', {}).get('plan', 'free') if 'Item' in sub_resp else 'free'
                if plan not in ['premium', 'pro', 'business', 'starter', 'testing']:
                    return {
                        'statusCode': 403,
                        'headers': headers,
                        'body': json.dumps({'error': 'Agent access requires premium plan'})
                    }
            
            # Execute agent
            if agent_type == 'email':
                result = send_email_agent(params.get('to'), params.get('subject'), params.get('body'))
            elif agent_type == 'sheets':
                result = export_csv_agent(user_id, params.get('data'), params.get('filename'))
            elif agent_type == 'calendar':
                result = create_calendar_agent(params.get('title'), params.get('date'), params.get('time'))
            elif agent_type == 'save':
                result = save_document_agent(user_id, params.get('title'), content)
            elif agent_type == 'export':
                result = export_document_agent(user_id, content, params.get('format', 'txt'))
            elif agent_type == 'summary':
                result = summarize_agent(content)
            else:
                result = {'status': 'error', 'message': 'Unknown agent type'}
            
            # Track usage
            if user_id and result.get('status') == 'success':
                track_usage(user_id, 'agent')
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(result)
            }
        
        elif path == '/upload' and method == 'POST':
            body = json.loads(event['body'])
            # user_id comes from verified token
            filename = body.get('filename')
            content = body.get('content')
            s3_key = body.get('s3_key')  # For large files uploaded to S3
            
            # Check usage limits
            if user_id and not check_usage_limit(user_id, 'document'):
                return {
                    'statusCode': 403,
                    'headers': headers,
                    'body': json.dumps({'error': 'Document limit reached. Upgrade to continue.'})
                }
            
            # Handle S3-based PDF upload
            if s3_key:
                try:
                    obj = s3.get_object(Bucket='documentgpt-website-prod', Key=s3_key)
                    pdf_bytes = obj['Body'].read()
                    if PyPDF2:
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                        content = ''.join([page.extract_text() for page in pdf_reader.pages])
                    else:
                        content = pdf_bytes.decode('utf-8', errors='ignore')
                except Exception as e:
                    return {
                        'statusCode': 400,
                        'headers': headers,
                        'body': json.dumps({'error': f'PDF processing failed: {str(e)}'})
                    }
            
            # Save document to DynamoDB
            doc_id = save_document(user_id, filename, content)
            
            # Generate smart questions, insights, and highlights
            questions = generate_smart_questions(content)
            insights = generate_instant_insights(content)
            highlights = generate_smart_highlights(content)
            
            # Track usage
            if user_id:
                track_usage(user_id, 'document')
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'File uploaded successfully',
                    'doc_id': doc_id,
                    'questions': questions,
                    'insights': insights,
                    'highlights': highlights
                })
            }
        
        elif path == '/autocomplete' and method == 'POST':
            body = json.loads(event['body'])
            context = body.get('context', '')
            # user_id comes from verified token
            max_tokens = body.get('max_tokens', 15)
            
            if len(context) < 20:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Context too short'})
                }
            
            # Fast autocomplete with gpt-4o-mini
            word_count = max_tokens // 2  # Rough estimate: 2 tokens per word
            prompt = f"Continue this text with {word_count}-{word_count+3} words (respond with ONLY the continuation, no quotes): \"{context[-200:]}\""
            completion = openai_chat(prompt, use_mini=True, max_tokens=max_tokens*2)
            completion = completion.replace('"', '').replace("'", '').strip()
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'completion': completion})
            }
        
        elif path == '/live-assist' and method == 'POST':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'suggestions': ['Consider adding more detail here', 'This sentence could be clearer']
                })
            }
        
        elif path == '/subscription' and method == 'POST':
            body = json.loads(event['body'])
            action = body.get('action')
            # user_id comes from verified token
            plan = body.get('plan', 'monthly')
            
            if action == 'create':
                return create_stripe_checkout(user_id, plan, request_headers)
            elif action == 'status':
                return get_subscription_status(user_id, request_headers)
            elif action == 'cancel':
                return cancel_subscription(user_id, request_headers)
            elif action == 'portal':
                return create_billing_portal(user_id, request_headers)
        

        
        elif path == '/me' and method == 'GET':
            # user_id comes from verified token
            try:
                # Get user from Cognito
                cognito = boto3.client('cognito-idp', region_name=COGNITO_REGION)
                user_response = cognito.admin_get_user(
                    UserPoolId=COGNITO_USER_POOL_ID,
                    Username=user_id
                )
                
                # Extract user attributes
                user_attrs = {attr['Name']: attr['Value'] for attr in user_response.get('UserAttributes', [])}
                
                # Get subscription
                subscriptions_table = dynamodb.Table('documentgpt-subscriptions')
                sub_response = subscriptions_table.get_item(Key={'user_id': user_id})
                subscription = sub_response.get('Item', {}) if 'Item' in sub_response else {}
                
                # Get usage
                usage_table = dynamodb.Table('documentgpt-usage')
                usage_response = usage_table.get_item(Key={'user_id': user_id})
                usage = usage_response.get('Item', {}) if 'Item' in usage_response else {}
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'user_id': user_id,
                        'email': user_attrs.get('email'),
                        'name': user_attrs.get('name'),
                        'email_verified': user_attrs.get('email_verified') == 'true',
                        'plan': subscription.get('plan', 'free'),
                        'status': subscription.get('status', 'inactive'),
                        'billing_cycle': subscription.get('billing_cycle'),
                        'stripe_customer_id': subscription.get('stripe_customer_id'),
                        'usage': {
                            'chats_used': usage.get('chats_used', 0),
                            'documents_uploaded': usage.get('documents_uploaded', 0),
                            'agents_used': usage.get('agents_used', 0)
                        }
                    }, cls=DecimalEncoder)
                }
            except Exception as e:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': str(e)})
                }
        
        elif path == '/usage' and method == 'GET':
            # user_id comes from verified token
            result = get_usage_stats(user_id, request_headers)
            return {
                'statusCode': result['statusCode'],
                'headers': headers,
                'body': result['body']
            }
        
        elif path == '/documents' and method == 'GET':
            # user_id comes from verified token
            docs_table = dynamodb.Table(DOC_TABLE)
            response = docs_table.query(
                KeyConditionExpression='pk = :pk',
                ExpressionAttributeValues={':pk': f'USER#{user_id}'}
            )
            documents = [{
                'doc_id': item.get('doc_id'),
                'filename': item.get('filename'),
                'created_at': item.get('created_at'),
                'updated_at': item.get('updated_at'),
                'content': item.get('content', ''),
                'isPdf': item.get('isPdf', False),
                'chat_history': item.get('chat_history', [])
            } for item in response.get('Items', [])]
            documents.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'documents': documents})
            }
        
        elif path == '/documents' and method == 'POST':
            body = json.loads(event['body'])
            # user_id comes from verified token
            doc_id = body.get('doc_id')
            name = body.get('name')
            content = body.get('content', '')
            isPdf = body.get('isPdf', False)
            chat_history = body.get('chat_history', [])
            
            if not user_id or not doc_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'user_id and doc_id required'})
                }
            
            docs_table = dynamodb.Table(DOC_TABLE)
            docs_table.put_item(
                Item={
                    'pk': f'USER#{user_id}',
                    'sk': f'DOC#{doc_id}',
                    'doc_id': doc_id,
                    'filename': name,
                    'content': content[:120000],
                    'isPdf': isPdf,
                    'chat_history': chat_history[:50],
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            )
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'Document saved', 'doc_id': doc_id})
            }
        
        elif path.startswith('/documents/') and method == 'DELETE':
            doc_id = path.split('/')[-1]
            # user_id comes from verified token
            docs_table = dynamodb.Table(DOC_TABLE)
            docs_table.delete_item(Key={'pk': f'USER#{user_id}', 'sk': f'DOC#{doc_id}'})
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'Document deleted'})
            }
        
        elif path == '/upload-url' and method == 'POST':
            body = json.loads(event['body'])
            # user_id comes from verified token
            filename = body.get('filename')
            
            # Generate presigned URL for S3 upload
            key = f"uploads/{user_id}/{filename}"
            url = s3.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': 'documentgpt-website-prod',
                    'Key': key,
                    'ContentType': 'application/pdf'
                },
                ExpiresIn=300
            )
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'upload_url': url, 's3_key': key})
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

# DynamoDB cache for chat responses
cache_table = dynamodb.Table(DOC_TABLE)

def openai_chat(prompt, use_mini=False, max_tokens=150):
    """OpenAI chat with DynamoDB caching and gpt-4o-mini option"""
    # Check cache first
    cache_key = f"CACHE#{hash(prompt) % 1000000}"
    try:
        cache_resp = cache_table.get_item(Key={'pk': 'CHAT_CACHE', 'sk': cache_key})
        if 'Item' in cache_resp:
            cached = cache_resp['Item']
            # Check if cache is less than 1 hour old
            cached_time = datetime.fromisoformat(cached.get('cached_at', '2000-01-01'))
            if datetime.now() - cached_time < timedelta(hours=1):
                print(f"⚡ Cache hit for prompt")
                return cached['response']
    except:
        pass
    
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    system_prompt = """You are a smart, conversational AI assistant for DocumentGPT - a journaling and document tool.

KEY BEHAVIORS:
- Be SHORT and conversational (2-3 sentences max unless asked for more)
- When user asks you to DO something (clear, add, delete, etc), just confirm you'll do it
- NO bullet points or long lists unless specifically requested
- Talk like a helpful friend, not a tutorial
- If user says "push X to journal" or "add X", just say "Added!" or "Done!"
- If user says "clear my journal", just say "Cleared! Ready for a fresh start."
- If user says "undo", just say "Undone!"

EXAMPLES:
User: "clear my journal" → You: "Cleared! What would you like to write about?"
User: "give me an opening line about happiness" → You: "How about: 'Happiness isn't a destination, it's how you travel.' Want another?"
User: "push that to my journal" → You: "Added to your journal!"

Be BRIEF. Be HELPFUL. Be HUMAN."""
    
    # Use gpt-4o-mini for faster, cheaper responses
    model = 'gpt-4o-mini' if use_mini else 'gpt-4o'
    
    data = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': max_tokens,
        'temperature': 0.7,
        'stream': False
    }
    
    response = http.request('POST', url, body=json.dumps(data), headers=headers)
    result = json.loads(response.data.decode('utf-8'))
    
    if 'error' in result:
        error_msg = result['error'].get('message', 'Unknown error')
        return f"Sorry, I encountered an error: {error_msg}"
    
    if 'choices' in result and len(result['choices']) > 0:
        response_text = result['choices'][0]['message']['content']
        
        # Cache the response
        try:
            cache_table.put_item(
                Item={
                    'pk': 'CHAT_CACHE',
                    'sk': cache_key,
                    'response': response_text,
                    'cached_at': datetime.now().isoformat(),
                    'ttl': int((datetime.now() + timedelta(hours=24)).timestamp())
                }
            )
        except:
            pass
        
        return response_text
    else:
        return "Sorry, I couldn't process that request. Please try again."

def create_stripe_checkout(user_id, plan='monthly', request_headers=None):
    """Create Stripe Checkout Session"""
    cors_headers = make_headers(request_headers)
    if not stripe_secret:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Stripe not configured'})
        }
    
    try:
        # Determine price ID and mode based on plan
        if plan == 'test':
            price_id = STRIPE_TEST_PRICE_ID
            mode = 'payment'  # One-time payment for test
        elif plan == 'monthly':
            price_id = STRIPE_MONTHLY_PRICE_ID
            mode = 'subscription'
        else:
            price_id = STRIPE_ANNUAL_PRICE_ID
            mode = 'subscription'
        
        # Create Stripe Checkout Session
        url = 'https://api.stripe.com/v1/checkout/sessions'
        
        data = {
            'mode': mode,
            'line_items[0][price]': price_id,
            'line_items[0][quantity]': '1',
            'success_url': 'https://documentgpt.io/backup.html?success=true',
            'cancel_url': 'https://documentgpt.io/backup.html?canceled=true',
            'client_reference_id': user_id,
            'metadata[user_id]': user_id,
            'metadata[plan]': plan
        }
        
        # URL encode the data
        encoded_data = '&'.join([f'{k}={v}' for k, v in data.items()])
        stripe_headers = {
            'Authorization': f'Bearer {stripe_secret}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = http.request('POST', url, body=encoded_data, headers=stripe_headers)
        result = json.loads(response.data.decode('utf-8'))
        
        if 'id' in result:
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({
                    'checkout_url': result['url'],
                    'session_id': result['id']
                })
            }
        else:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': result.get('error', {}).get('message', 'Checkout failed')})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_stripe_webhook(event):
    """Handle Stripe webhook events with signature verification"""
    cors_headers = make_headers(event.get('headers'))
    try:
        body = event.get('body', '')
        sig_header = event.get('headers', {}).get('stripe-signature') or event.get('headers', {}).get('Stripe-Signature', '')
        
        # Get webhook secret from Secrets Manager
        try:
            webhook_secret = secretsmanager.get_secret_value(SecretId='documentgpt/stripe-webhook-secret')['SecretString']
        except:
            webhook_secret = None
        
        # Verify webhook signature if secret is configured
        if webhook_secret and sig_header:
            try:
                # Parse signature header
                sig_parts = dict(part.split('=') for part in sig_header.split(','))
                timestamp = sig_parts.get('t')
                signatures = [v for k, v in sig_parts.items() if k.startswith('v1')]
                
                # Compute expected signature
                import hmac
                import hashlib
                signed_payload = f"{timestamp}.{body}"
                expected_sig = hmac.new(
                    webhook_secret.encode('utf-8'),
                    signed_payload.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                # Verify signature
                if expected_sig not in signatures:
                    return {
                        'statusCode': 401,
                        'headers': cors_headers,
                        'body': json.dumps({'error': 'Invalid signature'})
                    }
                
                # Check timestamp (prevent replay attacks)
                current_time = int(datetime.now().timestamp())
                if abs(current_time - int(timestamp)) > 300:  # 5 minutes
                    return {
                        'statusCode': 401,
                        'headers': cors_headers,
                        'body': json.dumps({'error': 'Timestamp too old'})
                    }
            except Exception as e:
                return {
                    'statusCode': 401,
                    'headers': cors_headers,
                    'body': json.dumps({'error': f'Signature verification failed: {str(e)}'})
                }
        
        # Parse webhook payload
        webhook_data = json.loads(body)
        event_type = webhook_data.get('type')
        data = webhook_data.get('data', {}).get('object', {})
        
        subscriptions_table = dynamodb.Table('documentgpt-subscriptions')
        
        if event_type == 'checkout.session.completed':
            # Payment successful, activate subscription
            user_id = data.get('client_reference_id')
            customer_id = data.get('customer')
            subscription_id = data.get('subscription')
            plan = data.get('metadata', {}).get('plan', 'monthly')
            
            subscriptions_table.put_item(
                Item={
                    'user_id': user_id,
                    'plan': 'premium',
                    'billing_cycle': plan,
                    'status': 'active',
                    'stripe_customer_id': customer_id,
                    'stripe_subscription_id': subscription_id or 'test_payment',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            )
            
        elif event_type == 'customer.subscription.deleted':
            # Subscription canceled
            subscription_id = data.get('id')
            # Find user by subscription_id and update status
            # (Would need GSI on subscription_id for production)
            pass
        
        elif event_type == 'invoice.payment_failed':
            # Payment failed
            customer_id = data.get('customer')
            # Update subscription status to past_due
            pass
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'received': True})
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'error': str(e)})
        }

def create_billing_portal(user_id, request_headers=None):
    """Create Stripe Billing Portal session"""
    cors_headers = make_headers(request_headers)
    if not stripe_secret:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Stripe not configured'})
        }
    
    try:
        subscriptions_table = dynamodb.Table('documentgpt-subscriptions')
        response = subscriptions_table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'No subscription found'})
            }
        
        customer_id = response['Item'].get('stripe_customer_id')
        
        # Handle owner/lifetime accounts
        if customer_id in ['owner_account', 'lifetime', 'admin']:
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({
                    'message': 'Lifetime account - no billing to manage',
                    'is_lifetime': True
                })
            }
        
        # Create Billing Portal session
        url = 'https://api.stripe.com/v1/billing_portal/sessions'
        headers = {
            'Authorization': f'Bearer {stripe_secret}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'customer': customer_id,
            'return_url': 'https://documentgpt.io/backup.html'
        }
        
        encoded_data = '&'.join([f'{k}={v}' for k, v in data.items()])
        stripe_headers = {
            'Authorization': f'Bearer {stripe_secret}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        stripe_response = http.request('POST', url, body=encoded_data, headers=stripe_headers)
        result = json.loads(stripe_response.data.decode('utf-8'))
        
        if 'url' in result:
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'portal_url': result['url']})
            }
        else:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': result.get('error', {}).get('message', 'Portal creation failed')})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': str(e)})
        }

def cancel_subscription(user_id, request_headers=None):
    """Cancel user subscription"""
    cors_headers = make_headers(request_headers)
    if not stripe_secret:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Stripe not configured'})
        }
    
    try:
        subscriptions_table = dynamodb.Table('documentgpt-subscriptions')
        response = subscriptions_table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'No subscription found'})
            }
        
        subscription_id = response['Item'].get('stripe_subscription_id')
        
        # Cancel in Stripe
        url = f'https://api.stripe.com/v1/subscriptions/{subscription_id}'
        stripe_headers = {
            'Authorization': f'Bearer {stripe_secret}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        stripe_response = http.request('DELETE', url, headers=stripe_headers)
        
        # Update DynamoDB
        subscriptions_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET #status = :status, updated_at = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'canceled',
                ':updated': datetime.now().isoformat()
            }
        )
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'status': 'canceled'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': str(e)})
        }

def get_subscription_status(user_id, request_headers=None):
    """Get user subscription status"""
    cors_headers = make_headers(request_headers)
    try:
        subscriptions_table = dynamodb.Table('documentgpt-subscriptions')
        response = subscriptions_table.get_item(Key={'user_id': user_id})
        
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({
                    'plan': response['Item'].get('plan', 'free'),
                    'status': response['Item'].get('status', 'inactive')
                })
            }
        else:
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'plan': 'free', 'status': 'active'})
            }
    except Exception as e:
        return {'statusCode': 500, 'headers': cors_headers, 'body': json.dumps({'error': str(e)})}

def get_usage_stats(user_id, request_headers=None):
    """Get user usage statistics"""
    cors_headers = make_headers(request_headers)
    try:
        usage_table = dynamodb.Table('documentgpt-usage')
        response = usage_table.get_item(Key={'user_id': user_id})
        
        if 'Item' in response:
            usage = response['Item']
        else:
            usage = {'chats_used': 0, 'documents_uploaded': 0, 'agents_used': 0}
        
        # Get subscription to determine limits
        sub_response = get_subscription_status(user_id, request_headers)
        sub_data = json.loads(sub_response['body'])
        plan = sub_data.get('plan', 'free')
        
        limits = {
            'free': {'chats': 50, 'documents': 10, 'agents': 0},
            'premium': {'chats': -1, 'documents': -1, 'agents': -1},
            'testing': {'chats': -1, 'documents': -1, 'agents': -1}
        }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'usage': usage,
                'limits': limits.get(plan, limits['free']),
                'plan': plan
            }, cls=DecimalEncoder)
        }
    except Exception as e:
        return {'statusCode': 500, 'headers': cors_headers, 'body': json.dumps({'error': str(e)})}

def check_usage_limit(user_id, usage_type):
    """Check if user has exceeded usage limits"""
    try:
        # Get subscription
        subscriptions_table = dynamodb.Table('documentgpt-subscriptions')
        sub_response = subscriptions_table.get_item(Key={'user_id': user_id})
        plan = sub_response.get('Item', {}).get('plan', 'free') if 'Item' in sub_response else 'free'
        
        # Premium/Pro/Business/Testing = unlimited
        if plan in ['premium', 'pro', 'business', 'starter', 'testing']:
            return True
        
        # Get current usage
        usage_table = dynamodb.Table('documentgpt-usage')
        usage_response = usage_table.get_item(Key={'user_id': user_id})
        usage = usage_response.get('Item', {}) if 'Item' in usage_response else {}
        
        # Free tier limits
        limits = {'chat': 10, 'document': 2, 'agent': 0}
        current = usage.get(f'{usage_type}s_used', 0) if usage_type != 'chat' else usage.get('chats_used', 0)
        
        return current < limits.get(usage_type, 0)
    except:
        return True  # Allow on error

def get_current_usage(user_id, usage_type):
    """Get current usage count for a specific type"""
    try:
        usage_table = dynamodb.Table('documentgpt-usage')
        usage_response = usage_table.get_item(Key={'user_id': user_id})
        usage = usage_response.get('Item', {}) if 'Item' in usage_response else {}
        return usage.get(f'{usage_type}s_used', 0) if usage_type != 'chat' else usage.get('chats_used', 0)
    except:
        return 0

def track_event(user_id, event_type, metadata=None):
    """Track analytics events in usage table"""
    try:
        usage_table = dynamodb.Table('documentgpt-usage')
        response = usage_table.get_item(Key={'user_id': user_id})
        
        if 'Item' in response:
            current = response['Item']
        else:
            current = {
                'user_id': user_id,
                'chats_used': 0,
                'documents_uploaded': 0,
                'agents_used': 0,
                'last_reset': datetime.now().replace(day=1).isoformat()
            }
        
        # Track events in array
        if 'events' not in current:
            current['events'] = []
        
        current['events'].append({
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })
        
        # Keep only last 100 events
        if len(current['events']) > 100:
            current['events'] = current['events'][-100:]
        
        usage_table.put_item(Item=current)
        return True
    except Exception as e:
        print(f"Event tracking error: {e}")
        return False

def track_usage(user_id, usage_type):
    """Track user usage"""
    try:
        usage_table = dynamodb.Table('documentgpt-usage')
        response = usage_table.get_item(Key={'user_id': user_id})
        
        if 'Item' in response:
            current = response['Item']
        else:
            current = {
                'user_id': user_id,
                'chats_used': 0,
                'documents_uploaded': 0,
                'agents_used': 0,
                'last_reset': datetime.now().replace(day=1).isoformat()
            }
        
        if usage_type == 'chat':
            current['chats_used'] = current.get('chats_used', 0) + 1
        elif usage_type == 'document':
            current['documents_uploaded'] = current.get('documents_uploaded', 0) + 1
        elif usage_type == 'agent':
            current['agents_used'] = current.get('agents_used', 0) + 1
        
        usage_table.put_item(Item=current)
        return True
    except Exception as e:
        print(f"Usage tracking error: {e}")
        return False

def save_document(user_id, filename, content):
    """Save document to DynamoDB"""
    doc_id = f"doc_{int(datetime.now().timestamp())}"
    docs_table = dynamodb.Table(DOC_TABLE)
    docs_table.put_item(
        Item={
            'pk': f"USER#{user_id}",
            'sk': f"DOC#{doc_id}",
            'doc_id': doc_id,
            'filename': filename,
            'content': content[:120000],  # Limit to ~20K words
            'created_at': datetime.now().isoformat()
        }
    )
    return doc_id

def generate_smart_questions(content):
    """Generate AI-powered questions from document content"""
    prompt = f"Analyze this document and generate 4-5 specific, insightful questions someone might ask about it. Return only the questions as a JSON array.\n\nDocument:\n{content[:2000]}"
    
    try:
        response = openai_chat(prompt)
        # Try to parse as JSON, fallback to simple list
        if '[' in response and ']' in response:
            start = response.index('[')
            end = response.rindex(']') + 1
            questions = json.loads(response[start:end])
            return questions[:5]
    except:
        pass
    
    return [
        "What are the key points in this document?",
        "Can you summarize the main findings?",
        "What are the important dates or deadlines?",
        "Who are the key people or entities mentioned?"
    ]

def generate_instant_insights(content):
    """Generate instant insights: key points, action items, questions"""
    prompt = f"""Analyze this document and provide instant insights in JSON format:
{{
  "keyPoints": ["3 most important points"],
  "actionItems": ["2 action items or next steps"],
  "questions": ["3 questions to explore"]
}}

Document:
{content[:3000]}"""
    
    try:
        response = openai_chat(prompt)
        if '{' in response and '}' in response:
            start = response.index('{')
            end = response.rindex('}') + 1
            insights = json.loads(response[start:end])
            return insights
    except:
        pass
    
    return {
        "keyPoints": ["Document uploaded successfully", "Ready for analysis", "Ask questions to learn more"],
        "actionItems": ["Review the document", "Ask specific questions"],
        "questions": ["What are the main topics?", "Are there any deadlines?", "Who is involved?"]
    }

def send_email_agent(to_email, subject, body):
    """Send email via AWS SES"""
    try:
        ses.send_email(
            Source='noreply@documentgpt.io',
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        return {'status': 'success', 'message': f'Email sent to {to_email}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def export_csv_agent(user_id, data, filename):
    """Export data to CSV and upload to S3"""
    try:
        csv_content = data  # Assume data is already CSV formatted
        key = f"exports/{user_id}/{filename}"
        s3.put_object(Bucket='documentgpt-website-prod', Key=key, Body=csv_content, ContentType='text/csv')
        url = f"https://documentgpt-website-prod.s3.amazonaws.com/{key}"
        return {'status': 'success', 'download_url': url}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def create_calendar_agent(title, date, time):
    """Generate iCal file for calendar event"""
    ical = f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:{title}
DTSTART:{date}T{time.replace(':', '')}00
DURATION:PT1H
END:VEVENT
END:VCALENDAR"""
    ical_base64 = base64.b64encode(ical.encode()).decode()
    return {'status': 'success', 'ical_data': ical_base64}

def save_document_agent(user_id, title, content):
    """Save document to user's library"""
    doc_id = save_document(user_id, title, content)
    return {'status': 'success', 'doc_id': doc_id}

def export_document_agent(user_id, content, format_type):
    """Export document in specified format"""
    try:
        filename = f"document_{int(datetime.now().timestamp())}.{format_type}"
        key = f"exports/{user_id}/{filename}"
        
        if format_type == 'txt':
            s3.put_object(Bucket='documentgpt-website-prod', Key=key, Body=content, ContentType='text/plain')
        elif format_type == 'pdf':
            # Simple text-to-PDF (would need proper library for production)
            s3.put_object(Bucket='documentgpt-website-prod', Key=key, Body=content, ContentType='application/pdf')
        
        url = f"https://documentgpt-website-prod.s3.amazonaws.com/{key}"
        return {'status': 'success', 'download_url': url}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def summarize_agent(content):
    """Summarize document content"""
    prompt = f"Provide a concise summary of this document in 3-5 bullet points:\n\n{content[:3000]}"
    summary = openai_chat(prompt)
    return {'status': 'success', 'summary': summary}

def generate_smart_highlights(content):
    """Generate smart highlights for key sentences/phrases"""
    prompt = f"""Identify 10-15 important sentences or phrases from this document to highlight. Return JSON array:
[{{"text": "exact phrase", "type": "key|action|important"}}]

Document:
{content[:5000]}"""
    
    try:
        response = openai_chat(prompt)
        if '[' in response and ']' in response:
            start = response.index('[')
            end = response.rindex(']') + 1
            highlights = json.loads(response[start:end])
            return highlights[:15]
    except:
        pass
    
    return []
