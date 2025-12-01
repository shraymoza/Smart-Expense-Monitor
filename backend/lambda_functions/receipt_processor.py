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
            
            # Extract text from receipt using Textract (if enabled)
            extracted_text = ""
            if ENABLE_TEXTRACT:
                extracted_text = extract_text_from_receipt(bucket, key)
            
            # Parse receipt data (simplified - implement actual parsing logic)
            receipt_data = parse_receipt_data(extracted_text, key)
            
            # Save to DynamoDB
            save_receipt_metadata(key, receipt_data)
            
            if receipt_data.get('expense_data'):
                save_expense(receipt_data['expense_data'])
            
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


def handle_api_event(event):
    """Handle API Gateway requests"""
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    
    if http_method == 'GET' and '/expenses' in path:
        return get_expenses(event)
    elif http_method == 'POST' and '/receipts' in path:
        return upload_receipt(event)
    else:
        return {
            'statusCode': 404,
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


def parse_receipt_data(text, key):
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
        's3Key': key,
        'uploadDate': upload_date,
        'extractedText': text[:500],  # Store first 500 chars
        'expense_data': {
            'expenseId': receipt_id,
            'amount': 0.0,  # Extract from text
            'storeName': 'Unknown Store',  # Extract from text
            'date': upload_date,
            'category': 'Other'
        }
    }


def save_receipt_metadata(key, receipt_data):
    """Save receipt metadata to DynamoDB"""
    item = {
        'receiptId': receipt_data['receiptId'],
        'userId': 'user-placeholder',  # Extract from S3 key or context
        's3Key': key,
        'uploadDate': receipt_data['uploadDate'],
        'extractedText': receipt_data.get('extractedText', ''),
        'status': 'processed'
    }
    
    receipts_table.put_item(Item=item)
    print(f"Saved receipt metadata: {receipt_data['receiptId']}")


def save_expense(expense_data):
    """Save expense to DynamoDB"""
    expense_data['userId'] = 'user-placeholder'  # Extract from context
    expense_data['expenseId'] = expense_data.get('expenseId', str(uuid.uuid4()))
    expense_data['createdAt'] = datetime.utcnow().isoformat()
    
    expenses_table.put_item(Item=expense_data)
    print(f"Saved expense: {expense_data['expenseId']}")


def get_expenses(event):
    """Get expenses for a user"""
    # TODO: Extract userId from Cognito token
    userId = 'user-placeholder'
    
    try:
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
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }


def upload_receipt(event):
    """Handle receipt upload via API"""
    # TODO: Implement presigned URL generation for S3 upload
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'message': 'Upload endpoint - to be implemented'})
    }

