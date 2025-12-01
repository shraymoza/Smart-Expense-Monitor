import json
import boto3
import os
from datetime import datetime
import uuid

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
textract_client = boto3.client('textract')

# Get table names from environment variables
EXPENSES_TABLE = os.environ.get('EXPENSES_TABLE_NAME')
RECEIPTS_TABLE = os.environ.get('RECEIPTS_TABLE_NAME')
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
ENABLE_TEXTRACT = os.environ.get('ENABLE_TEXTRACT', 'false').lower() == 'true'

expenses_table = dynamodb.Table(EXPENSES_TABLE)
receipts_table = dynamodb.Table(RECEIPTS_TABLE)


def lambda_handler(event, context):
    """
    Lambda handler for processing receipts.
    Can be triggered by:
    1. S3 event (when receipt is uploaded)
    2. API Gateway (for manual processing)
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Handle S3 event
    if 'Records' in event:
        return handle_s3_event(event)
    
    # Handle API Gateway event
    if 'httpMethod' in event or 'requestContext' in event:
        return handle_api_event(event)
    
    return {
        'statusCode': 400,
        'body': json.dumps({'message': 'Invalid event type'})
    }


def handle_s3_event(event):
    """Process S3 upload event"""
    try:
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            print(f"Processing receipt: s3://{bucket}/{key}")
            
            # Extract userId from S3 key path: users/{userId}/uploads/{filename}
            # Example: users/user-123/uploads/receipt.jpg -> userId = user-123
            userId = extract_user_id_from_key(key)
            if not userId:
                print(f"Warning: Could not extract userId from key: {key}")
                continue
            
            print(f"Extracted userId: {userId}")
            
            # Extract text from receipt using Textract (if enabled)
            extracted_text = ""
            if ENABLE_TEXTRACT:
                extracted_text = extract_text_from_receipt(bucket, key)
            
            # Parse receipt data (simplified - implement actual parsing logic)
            receipt_data = parse_receipt_data(extracted_text, key, userId)
            
            # Save to DynamoDB
            save_receipt_metadata(key, receipt_data, userId)
            
            if receipt_data.get('expense_data'):
                save_expense(receipt_data['expense_data'], userId)
            
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Receipt processed successfully'})
        }
    except Exception as e:
        print(f"Error processing receipt: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Error: {str(e)}'})
        }


def extract_user_id_from_key(key):
    """
    Extract userId from S3 key path.
    Expected format: users/{userId}/uploads/{filename}
    Returns userId or None if format is invalid
    """
    try:
        # Split the key by '/'
        parts = key.split('/')
        
        # Should have at least: ['users', '{userId}', 'uploads', '{filename}']
        if len(parts) >= 3 and parts[0] == 'users':
            userId = parts[1]
            return userId
        else:
            print(f"Invalid key format. Expected: users/{{userId}}/uploads/{{filename}}, Got: {key}")
            return None
    except Exception as e:
        print(f"Error extracting userId from key {key}: {str(e)}")
        return None


def handle_api_event(event):
    """Handle API Gateway requests"""
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    resource = event.get('resource', '')
    path_parameters = event.get('pathParameters') or {}
    
    # Log for debugging
    print(f"API Event - Method: {http_method}, Path: {path}, Resource: {resource}")
    
    # Handle different endpoints
    # Check both path and resource (API Gateway uses resource for routing)
    if http_method == 'GET':
        if '/expenses' in path or '/expenses' in resource:
            if path_parameters.get('id'):
                return get_expense(event, path_parameters['id'])
            return get_expenses(event)
    
    elif http_method == 'POST':
        if '/receipts' in path or '/receipts' in resource or resource == '/receipts':
            print("Calling upload_receipt function")
            return upload_receipt(event)
    
    # Default 404
    print(f"No handler found for {http_method} {path} (resource: {resource})")
    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'message': 'Not found'})
    }


def extract_text_from_receipt(bucket, key):
    """Extract text from receipt using AWS Textract"""
    try:
        response = textract_client.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        # Extract text blocks
        text_blocks = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block.get('Text', ''))
        
        return '\n'.join(text_blocks)
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        return ""


def parse_receipt_data(text, key, userId):
    """Parse receipt data from extracted text"""
    # TODO: Implement actual receipt parsing logic
    # This is a placeholder that extracts basic information
    
    receipt_id = str(uuid.uuid4())
    upload_date = datetime.utcnow().isoformat()
    
    # Extract basic info (simplified)
    # In production, use ML/NLP to extract:
    # - Store name
    # - Date
    # - Total amount
    # - Items purchased
    
    return {
        'receiptId': receipt_id,
        'userId': userId,
        's3Key': key,
        'uploadDate': upload_date,
        'extractedText': text[:500],  # Store first 500 chars
        'expense_data': {
            'expenseId': receipt_id,
            'userId': userId,
            'amount': 0.0,  # Extract from text
            'storeName': 'Unknown Store',  # Extract from text
            'date': upload_date,
            'category': 'Other'
        }
    }


def save_receipt_metadata(key, receipt_data, userId):
    """Save receipt metadata to DynamoDB"""
    item = {
        'receiptId': receipt_data['receiptId'],
        'userId': userId,  # User ID extracted from S3 key path
        's3Key': key,
        'uploadDate': receipt_data['uploadDate'],
        'extractedText': receipt_data.get('extractedText', ''),
        'status': 'processed'
    }
    
    receipts_table.put_item(Item=item)
    print(f"Saved receipt metadata for user {userId}: {receipt_data['receiptId']}")


def save_expense(expense_data, userId):
    """Save expense to DynamoDB"""
    expense_data['userId'] = userId  # User ID extracted from S3 key path
    expense_data['expenseId'] = expense_data.get('expenseId', str(uuid.uuid4()))
    expense_data['createdAt'] = datetime.utcnow().isoformat()
    
    expenses_table.put_item(Item=expense_data)
    print(f"Saved expense for user {userId}: {expense_data['expenseId']}")


def get_expenses(event):
    """Get expenses for a user"""
    # Extract userId from Cognito token in API Gateway authorizer context
    # The userId is passed via the authorizer context
    try:
        # Get userId from authorizer context (set by Cognito authorizer)
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        
        # Cognito user ID format: sub claim or cognito:username
        userId = claims.get('sub') or claims.get('cognito:username')
        
        if not userId:
            # Fallback: try to get from query parameters (for testing)
            userId = event.get('queryStringParameters', {}).get('userId') if event.get('queryStringParameters') else None
            if not userId:
                return {
                    'statusCode': 401,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': 'User ID not found in request'})
                }
        
        print(f"Fetching expenses for user: {userId}")
        
        response = expenses_table.query(
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={
                ':userId': userId
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response.get('Items', []))
        }
    except Exception as e:
        print(f"Error fetching expenses: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': str(e)})
        }


def get_expense(event, expenseId):
    """Get a specific expense by ID"""
    try:
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        userId = claims.get('sub') or claims.get('cognito:username')
        
        if not userId:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'User ID not found in request'})
            }
        
        response = expenses_table.get_item(
            Key={
                'userId': userId,
                'expenseId': expenseId
            }
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Expense not found'})
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response['Item'])
        }
    except Exception as e:
        print(f"Error fetching expense: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': str(e)})
        }


def upload_receipt(event):
    """Generate presigned URL for S3 upload"""
    try:
        # Get userId from Cognito token
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        userId = claims.get('sub') or claims.get('cognito:username')
        
        if not userId:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'User ID not found in request'})
            }
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        fileName = body.get('fileName')
        fileType = body.get('fileType', 'application/octet-stream')
        
        if not fileName:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'fileName is required'})
            }
        
        # Ensure fileName follows user-specific path format
        if not fileName.startswith(f'users/{userId}/'):
            fileName = f'users/{userId}/uploads/{fileName.split("/")[-1]}'
        
        # Generate presigned URL (valid for 5 minutes)
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': fileName,
                'ContentType': fileType
            },
            ExpiresIn=300  # 5 minutes
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'uploadUrl': presigned_url,
                'fileName': fileName,
                'expiresIn': 300
            })
        }
    except Exception as e:
        print(f"Error generating presigned URL: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': str(e)})
        }

