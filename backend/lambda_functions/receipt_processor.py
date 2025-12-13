import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
import uuid
import re

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
textract_client = boto3.client('textract')


def decimal_default(obj):
    """JSON encoder helper to convert Decimal to float"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# Get table names from environment variables
EXPENSES_TABLE = os.environ.get('EXPENSES_TABLE_NAME')
RECEIPTS_TABLE = os.environ.get('RECEIPTS_TABLE_NAME')
USER_SETTINGS_TABLE = os.environ.get('USER_SETTINGS_TABLE_NAME')
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
ENABLE_TEXTRACT = os.environ.get('ENABLE_TEXTRACT', 'false').lower() == 'true'

expenses_table = dynamodb.Table(EXPENSES_TABLE)
receipts_table = dynamodb.Table(RECEIPTS_TABLE)
user_settings_table = dynamodb.Table(USER_SETTINGS_TABLE) if USER_SETTINGS_TABLE else None


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
                print(f"Textract is enabled. Extracting text from receipt...")
                extracted_text = extract_text_from_receipt(bucket, key)
            else:
                print("Textract is disabled. Skipping text extraction.")
            
            # Parse receipt data (simplified - implement actual parsing logic)
            receipt_data = parse_receipt_data(extracted_text, key, userId)
            
            # Save to DynamoDB
            save_receipt_metadata(key, receipt_data, userId)
            
            if receipt_data.get('expense_data'):
                save_expense(receipt_data['expense_data'], userId)
                # Trigger expense check immediately after saving (async, don't wait)
                trigger_expense_check(userId)
            
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
        elif '/settings' in path or '/settings' in resource:
            return get_user_settings(event)
    
    elif http_method == 'POST':
        if '/receipts' in path or '/receipts' in resource or resource == '/receipts':
            print("Calling upload_receipt function")
            return upload_receipt(event)
    
    elif http_method == 'PUT':
        if '/expenses' in path or '/expenses' in resource:
            if path_parameters.get('id'):
                return update_expense(event, path_parameters['id'])
        elif '/settings' in path or '/settings' in resource:
            return update_user_settings(event)
    
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
        print(f"Starting Textract extraction for s3://{bucket}/{key}")
        response = textract_client.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        print(f"Textract response received. Block count: {len(response.get('Blocks', []))}")
        
        # Extract text blocks
        text_blocks = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text = block.get('Text', '')
                text_blocks.append(text)
        
        extracted_text = '\n'.join(text_blocks)
        text_length = len(extracted_text)
        print(f"Textract extraction complete. Extracted {text_length} characters, {len(text_blocks)} lines")
        
        # Log first 200 characters for debugging
        if extracted_text:
            preview = extracted_text[:200].replace('\n', ' ')
            print(f"Extracted text preview (first 200 chars): {preview}...")
        else:
            print("Warning: No text extracted from receipt")
        
        return extracted_text
    except Exception as e:
        print(f"Error extracting text with Textract: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return ""


def parse_receipt_data(text, key, userId):
    """Parse receipt data from extracted text"""
    receipt_id = str(uuid.uuid4())
    upload_date = datetime.utcnow().isoformat()
    
    # Normalize text for easier parsing
    text_upper = text.upper() if text else ""
    text_lower = text.lower() if text else ""
    lines = text.split('\n') if text else []
    
    # Extract store name (common patterns)
    store_name = 'Unknown Store'
    common_stores = {
        'walmart': 'Walmart',
        'target': 'Target',
        'costco': 'Costco',
        'amazon': 'Amazon',
        'starbucks': 'Starbucks',
        'mcdonald': "McDonald's",
        'subway': 'Subway',
        'cvs': 'CVS',
        'walgreens': 'Walgreens',
        'home depot': 'Home Depot',
        'lowes': "Lowe's",
        'best buy': 'Best Buy',
        'kroger': 'Kroger',
        'safeway': 'Safeway',
        'whole foods': 'Whole Foods',
        'trader joe': "Trader Joe's",
        'aldi': 'Aldi',
        'publix': 'Publix',
        'rite aid': 'Rite Aid',
        'dollar general': 'Dollar General',
        'family dollar': 'Family Dollar',
        '7-eleven': '7-Eleven',
        'shell': 'Shell',
        'exxon': 'Exxon',
        'bp': 'BP',
        'chevron': 'Chevron',
        'mobil': 'Mobil'
    }
    
    # Check first 10 lines for store name
    for line in lines[:10]:
        line_lower = line.lower().strip()
        for store_key, store_value in common_stores.items():
            if store_key in line_lower:
                store_name = store_value
                print(f"Found store name: {store_name}")
                break
        if store_name != 'Unknown Store':
            break
    
    # Extract total amount (look for patterns like TOTAL, AMOUNT DUE, etc.)
    amount = Decimal('0.0')

    # 1) Strong match: TOTAL on same or next line
    total_match = re.search(
        r'TOTAL[^\d\n]*\$?\s*(\d+\.\d{2})',  # TOTAL $1.34  or  TOTAL 1.34
        text_upper,
        re.IGNORECASE
    )
    if not total_match:
        # Handles:
        # TOTAL
        # $1.34
        total_match = re.search(
            r'TOTAL[^\d\n]*\n\s*\$?\s*(\d+\.\d{2})',
            text_upper,
            re.IGNORECASE
        )

    if total_match:
        amount = Decimal(total_match.group(1))
        print(f"Found amount from TOTAL block: ${amount}")
    else:
        # 2) Fallback: scan lines from bottom, but ONLY lines that look like totals
        amount_patterns = [
            r'total\s*:?\s*\$?\s*(\d+\.\d{2})',
            r'total\s+amount\s*:?\s*\$?\s*(\d+\.\d{2})',
            r'amount\s+due\s*:?\s*\$?\s*(\d+\.\d{2})',
            r'grand\s+total\s*:?\s*\$?\s*(\d+\.\d{2})',
            r'balance\s+due\s*:?\s*\$?\s*(\d+\.\d{2})',
            r'\$\s*(\d+\.\d{2})\s*$',          # "$123.45" at end of line
            r'total\s+(\d+\.\d{2})',
        ]
        total_keywords = ('TOTAL', 'AMOUNT DUE', 'GRAND TOTAL', 'BALANCE DUE')

        for line in reversed(lines):
            line_upper = line.upper().strip()
            if not any(k in line_upper for k in total_keywords):
                continue
            for pattern in amount_patterns:
                match = re.search(pattern, line_upper, re.IGNORECASE)
                if match:
                    try:
                        amount = Decimal(match.group(1))
                        print(f"Found amount from fallback scan: ${amount}")
                        break
                    except (ValueError, IndexError):
                        continue
            if amount > 0:
                break

    # 3) Last resort: largest reasonable amount (ignore tiny discounts)
    if amount == 0 and text_upper:
        dollar_amounts = []
        for line in lines:
            up = line.upper()
            # Skip obvious non-total lines
            if any(k in up for k in ['DISCOUNT', 'CHANGE', 'CASH', 'PAYMENT', 'TAX', 'SUBTOTAL']):
                continue
            dollar_amounts.extend(re.findall(r'\$?\s*(\d+\.\d{2})', up))

        if dollar_amounts:
            try:
                amounts = [Decimal(amt) for amt in dollar_amounts]
                amount = max(amounts)
                print(f"Found largest amount as fallback: ${amount}")
            except (ValueError, TypeError):
                pass

    
    # Extract date (look for date patterns)
    receipt_date = upload_date  # Default to upload date
    
    # Date patterns: MM/DD/YYYY, MM-DD-YYYY, YYYY-MM-DD, etc.
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY or MM-DD-YYYY
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})',  # MM/DD/YY or MM-DD-YY
    ]
    
    for line in lines[:20]:  # Check first 20 lines
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # YYYY-MM-DD format
                        year, month, day = groups[0], groups[1], groups[2]
                    else:  # MM-DD-YYYY format
                        month, day, year = groups[0], groups[1], groups[2]
                        if len(year) == 2:
                            year = '20' + year
                    
                    receipt_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    print(f"Found receipt date: {receipt_date}")
                    break
                except (ValueError, IndexError):
                    continue
        if receipt_date != upload_date:
            break
    
    # Categorize based on store name
    category = 'Other'
    if store_name != 'Unknown Store':
        store_lower = store_name.lower()
        if any(x in store_lower for x in ['walmart', 'target', 'costco', 'kroger', 'safeway', 'whole foods', 'trader joe', 'aldi', 'publix']):
            category = 'Groceries'
        elif any(x in store_lower for x in ['starbucks', 'mcdonald', 'subway']):
            category = 'Food & Drink'
        elif any(x in store_lower for x in ['cvs', 'walgreens', 'rite aid']):
            category = 'Pharmacy'
        elif any(x in store_lower for x in ['home depot', 'lowes']):
            category = 'Home Improvement'
        elif any(x in store_lower for x in ['best buy']):
            category = 'Electronics'
        elif any(x in store_lower for x in ['shell', 'exxon', 'bp', 'chevron', 'mobil', '7-eleven']):
            category = 'Gas & Fuel'
        elif any(x in store_lower for x in ['amazon']):
            category = 'Shopping'
        elif any(x in store_lower for x in ['dollar general', 'family dollar']):
            category = 'Discount Store'
    
    # Extract individual items from receipt
    items = extract_items_from_receipt(lines, text_upper, amount)
    
    print(f"Parsed receipt - Store: {store_name}, Amount: ${amount}, Date: {receipt_date}, Category: {category}, Items: {len(items)}")
    
    return {
        'receiptId': receipt_id,
        'userId': userId,
        's3Key': key,
        'uploadDate': upload_date,
        'extractedText': text[:500] if text else '',  # Store first 500 chars
        'expense_data': {
            'expenseId': receipt_id,
            'userId': userId,
            'amount': amount,  # Already Decimal
            'storeName': store_name,
            'date': receipt_date,
            'category': category,
            'items': items  # List of items
        }
    }


def extract_items_from_receipt(lines, text_upper, total_amount):
    """Extract individual items from receipt text"""
    items = []
    
    if not lines:
        return items
    
    # Common patterns for item lines:
    # - Item name followed by price: "Milk $3.99"
    # - Item name and price on same line: "Bread 2.50"
    # - Item with quantity: "2x Apples $5.98"
    
    # Skip header lines (store name, address, etc.) and footer lines (total, tax, etc.)
    skip_keywords = [
        'TOTAL', 'SUBTOTAL', 'TAX', 'AMOUNT', 'DUE', 'CHANGE', 'CASH', 'CARD',
        'THANK', 'RECEIPT', 'STORE', 'ADDRESS', 'PHONE', 'DATE', 'TIME',
        'ITEM', 'DESCRIPTION', 'PRICE', 'QTY', 'QUANTITY'
    ]
    
    # Find where items section likely starts (after header)
    item_start_idx = 0
    for i, line in enumerate(lines[:15]):
        line_upper = line.upper().strip()
        # Look for section headers that might indicate start of items
        if any(keyword in line_upper for keyword in ['ITEM', 'DESCRIPTION', 'PRODUCT']):
            item_start_idx = i + 1
            break
        # Or start after store name/header (usually first 3-5 lines)
        if i > 5 and '$' in line or re.search(r'\d+\.\d{2}', line):
            item_start_idx = i
            break
    
    # Find where items section likely ends (before totals)
    item_end_idx = len(lines)
    for i in range(len(lines) - 1, max(0, len(lines) - 20), -1):
        line_upper = lines[i].upper().strip()
        if any(keyword in line_upper for keyword in ['TOTAL', 'SUBTOTAL', 'TAX', 'AMOUNT DUE']):
            item_end_idx = i
            break
    
    # Extract items from the middle section
    item_lines = lines[item_start_idx:item_end_idx]
    
    for line in item_lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        line_upper = line.upper()
        
        # Skip if it's a header/footer keyword
        if any(keyword in line_upper for keyword in skip_keywords):
            continue
        
        # Look for price patterns in the line
        price_patterns = [
            r'\$?\s*(\d+\.\d{2})\s*$',  # Price at end: "Item $12.99"
            r'\$\s*(\d+\.\d{2})',  # Price with $: "Item $12.99"
            r'(\d+\.\d{2})\s*$',  # Price at end without $: "Item 12.99"
        ]
        
        item_price = None
        item_name = None
        
        for pattern in price_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    price = Decimal(match.group(1))
                    # Only consider reasonable prices (between $0.01 and $1000)
                    if 0.01 <= price <= 1000:
                        item_price = price
                        # Extract item name (everything before the price)
                        item_name = line[:match.start()].strip()
                        break
                except (ValueError, IndexError):
                    continue
        
        # If we found a price, create an item
        if item_price and item_name:
            # Clean up item name
            item_name = re.sub(r'\s+', ' ', item_name)  # Remove extra spaces
            item_name = item_name.strip()
            
            # Skip if name is too short or looks like a price/date
            if len(item_name) < 2 or re.match(r'^\d+[\.\-\/]', item_name):
                continue
            
            # Check for quantity (e.g., "2x Milk" or "3 @ $2.99")
            quantity = Decimal('1.0')
            qty_patterns = [
                r'^(\d+)\s*x\s+',  # "2x Item"
                r'^(\d+)\s*@\s*',  # "2 @ Item"
                r'^(\d+)\s+',  # "2 Item"
            ]
            
            for qty_pattern in qty_patterns:
                qty_match = re.search(qty_pattern, item_name, re.IGNORECASE)
                if qty_match:
                    try:
                        quantity = Decimal(qty_match.group(1))
                        item_name = re.sub(qty_pattern, '', item_name, flags=re.IGNORECASE).strip()
                    except (ValueError, IndexError):
                        pass
                    break
            
            items.append({
                'name': item_name,
                'price': item_price,
                'quantity': quantity,
                'subtotal': item_price * quantity
            })
    
    # If we found items, validate and clean up
    if items:
        # Remove duplicates (same name and price)
        seen = set()
        unique_items = []
        for item in items:
            key = (item['name'].lower(), float(item['price']))
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        items = unique_items
        
        # Calculate total from items and compare with receipt total
        items_total = sum(item['subtotal'] for item in items)
        if total_amount > 0:
            # If items total is close to receipt total (within 10%), we're good
            if abs(float(items_total) - float(total_amount)) / float(total_amount) > 0.1:
                print(f"Warning: Items total (${items_total}) doesn't match receipt total (${total_amount})")
        
        print(f"Extracted {len(items)} items from receipt")
        for item in items[:5]:  # Log first 5 items
            print(f"  - {item['name']}: ${item['price']} x {item['quantity']} = ${item['subtotal']}")
    else:
        print("No items extracted from receipt")
    
    return items


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


def trigger_expense_check(userId):
    """Trigger expense notification check for a specific user"""
    try:
        lambda_client = boto3.client('lambda')
        notifier_function_name = os.environ.get('NOTIFIER_FUNCTION_NAME', '')
        
        if not notifier_function_name:
            print("NOTIFIER_FUNCTION_NAME not set, skipping expense check")
            return
        
        # Invoke notifier Lambda with userId directly
        lambda_client.invoke(
            FunctionName=notifier_function_name,
            InvocationType='Event',  # Async invocation - don't wait for response
            Payload=json.dumps({
                'source': 'receipt_processor',
                'userId': userId,
                'trigger': 'receipt_upload'
            })
        )
        print(f"Triggered expense check for user {userId} after receipt upload")
    except Exception as e:
        print(f"Error triggering expense check for user {userId}: {str(e)}")
        # Don't fail the receipt processing if notification fails


def save_expense(expense_data, userId):
    """Save expense to DynamoDB"""
    expense_data['userId'] = userId  # User ID extracted from S3 key path
    expense_data['expenseId'] = expense_data.get('expenseId', str(uuid.uuid4()))
    expense_data['createdAt'] = datetime.utcnow().isoformat()
    
    # Convert float to Decimal for DynamoDB compatibility
    if 'amount' in expense_data and isinstance(expense_data['amount'], float):
        expense_data['amount'] = Decimal(str(expense_data['amount']))
    elif 'amount' in expense_data and not isinstance(expense_data['amount'], Decimal):
        # Handle string amounts or other types
        try:
            expense_data['amount'] = Decimal(str(expense_data['amount']))
        except (ValueError, TypeError):
            expense_data['amount'] = Decimal('0.0')
    
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
        
        # Convert Decimal to float for JSON serialization
        items = response.get('Items', [])
        for item in items:
            if 'amount' in item and isinstance(item['amount'], Decimal):
                item['amount'] = float(item['amount'])
            
            # Convert item prices and subtotals to float
            if 'items' in item and isinstance(item['items'], list):
                for expense_item in item['items']:
                    if 'price' in expense_item and isinstance(expense_item['price'], Decimal):
                        expense_item['price'] = float(expense_item['price'])
                    if 'quantity' in expense_item and isinstance(expense_item['quantity'], Decimal):
                        expense_item['quantity'] = float(expense_item['quantity'])
                    if 'subtotal' in expense_item and isinstance(expense_item['subtotal'], Decimal):
                        expense_item['subtotal'] = float(expense_item['subtotal'])
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(items, default=decimal_default)
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
        
        # Convert Decimal to float for JSON serialization
        item = response['Item']
        if 'amount' in item and isinstance(item['amount'], Decimal):
            item['amount'] = float(item['amount'])
        
        # Convert item prices and subtotals to float
        if 'items' in item and isinstance(item['items'], list):
            for expense_item in item['items']:
                if 'price' in expense_item and isinstance(expense_item['price'], Decimal):
                    expense_item['price'] = float(expense_item['price'])
                if 'quantity' in expense_item and isinstance(expense_item['quantity'], Decimal):
                    expense_item['quantity'] = float(expense_item['quantity'])
                if 'subtotal' in expense_item and isinstance(expense_item['subtotal'], Decimal):
                    expense_item['subtotal'] = float(expense_item['subtotal'])
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(item, default=decimal_default)
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


def update_expense(event, expenseId):
    """Update an expense (supports category and items updates)"""
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
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        new_category = body.get('category')
        new_items = body.get('items')
        
        # At least one field must be provided
        if not new_category and new_items is None:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Either category or items must be provided'})
            }
        
        # Check if expense exists and belongs to user
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
        
        expense = response['Item']
        update_expressions = []
        expression_attribute_names = {}
        expression_attribute_values = {}
        
        # Handle category update
        if new_category:
            # Validate category
            valid_categories = [
                'Groceries', 'Food & Drink', 'Pharmacy', 'Home Improvement',
                'Electronics', 'Gas & Fuel', 'Shopping', 'Discount Store', 'Other'
            ]
            if new_category not in valid_categories:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': f'Invalid category. Must be one of: {", ".join(valid_categories)}'})
                }
            
            update_expressions.append('#cat = :category')
            expression_attribute_names['#cat'] = 'category'
            expression_attribute_values[':category'] = new_category
        
        # Handle items update
        if new_items is not None:
            # Validate items structure
            if not isinstance(new_items, list):
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': 'Items must be an array'})
                }
            
            # Process and validate each item
            processed_items = []
            total_amount = Decimal('0.00')
            
            for item in new_items:
                if not isinstance(item, dict):
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({'message': 'Each item must be an object'})
                    }
                
                name = item.get('name', '').strip()
                quantity = float(item.get('quantity', 1))
                price = float(item.get('price', 0))
                
                if not name:
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({'message': 'Item name is required'})
                    }
                
                if quantity <= 0:
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({'message': 'Item quantity must be greater than 0'})
                    }
                
                if price < 0:
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({'message': 'Item price cannot be negative'})
                    }
                
                subtotal = Decimal(str(quantity * price)).quantize(Decimal('0.01'))
                total_amount += subtotal
                
                processed_items.append({
                    'name': name,
                    'quantity': Decimal(str(quantity)),
                    'price': Decimal(str(price)),
                    'subtotal': subtotal
                })
            
            # Update items and recalculate total amount
            update_expressions.append('#items = :items')
            update_expressions.append('#amount = :amount')
            expression_attribute_names['#items'] = 'items'
            expression_attribute_names['#amount'] = 'amount'
            expression_attribute_values[':items'] = processed_items
            expression_attribute_values[':amount'] = total_amount
        
        # Perform the update
        update_expression = 'SET ' + ', '.join(update_expressions)
        
        expenses_table.update_item(
            Key={
                'userId': userId,
                'expenseId': expenseId
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        # Convert response for JSON serialization
        updated_expense = expenses_table.get_item(
            Key={
                'userId': userId,
                'expenseId': expenseId
            }
        )['Item']
        
        # Convert Decimal to float for JSON
        if 'amount' in updated_expense and isinstance(updated_expense['amount'], Decimal):
            updated_expense['amount'] = float(updated_expense['amount'])
        
        if 'items' in updated_expense and isinstance(updated_expense['items'], list):
            for item in updated_expense['items']:
                if 'price' in item and isinstance(item['price'], Decimal):
                    item['price'] = float(item['price'])
                if 'quantity' in item and isinstance(item['quantity'], Decimal):
                    item['quantity'] = float(item['quantity'])
                if 'subtotal' in item and isinstance(item['subtotal'], Decimal):
                    item['subtotal'] = float(item['subtotal'])
        
        update_messages = []
        if new_category:
            update_messages.append(f'category updated to {new_category}')
        if new_items is not None:
            update_messages.append(f'{len(processed_items)} items updated')
        
        print(f"Updated expense {expenseId}: {', '.join(update_messages)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Expense updated successfully',
                'expenseId': expenseId,
                'expense': updated_expense
            }, default=decimal_default)
        }
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"Error updating expense: {str(e)}")
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


def get_user_settings(event):
    """Get user settings"""
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
        
        if not user_settings_table:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'User settings table not configured'})
            }
        
        print(f"Fetching settings for user: {userId}")
        
        try:
            response = user_settings_table.get_item(
                Key={'userId': userId}
            )
            
            if 'Item' in response:
                settings = response['Item']
                # Convert Decimal to float for JSON serialization
                if 'monthlyThreshold' in settings and isinstance(settings['monthlyThreshold'], Decimal):
                    settings['monthlyThreshold'] = float(settings['monthlyThreshold'])
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(settings, default=decimal_default)
                }
            else:
                # Return default settings if not found
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'userId': userId,
                        'monthlyThreshold': None,
                        'emailNotifications': False
                    })
                }
        except Exception as e:
            print(f"Error fetching user settings: {str(e)}")
            raise
            
    except Exception as e:
        print(f"Error in get_user_settings: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': str(e)})
        }


def update_user_settings(event):
    """Update user settings"""
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
        
        if not user_settings_table:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'User settings table not configured'})
            }
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        monthly_threshold = body.get('monthlyThreshold')
        email_notifications = body.get('emailNotifications', True)
        
        if monthly_threshold is None:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'monthlyThreshold is required'})
            }
        
        # Convert to Decimal for DynamoDB
        threshold_decimal = Decimal(str(monthly_threshold))
        
        print(f"Updating settings for user: {userId}, threshold: ${threshold_decimal}")
        
        # Get user email from Cognito claims
        user_email = claims.get('email', '')
        
        settings_item = {
            'userId': userId,
            'monthlyThreshold': threshold_decimal,
            'emailNotifications': email_notifications,
            'email': user_email,
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        user_settings_table.put_item(Item=settings_item)
        
        # Convert back to float for response
        settings_item['monthlyThreshold'] = float(threshold_decimal)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(settings_item, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error updating user settings: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': str(e)})
        }

