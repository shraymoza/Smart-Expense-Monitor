import json
import boto3
import os
import time
from datetime import datetime
from decimal import Decimal
import uuid
import re

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
textract_client = boto3.client('textract')
cloudwatch = boto3.client('cloudwatch')


def decimal_default(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def publish_metric(metric_name, value, unit='Count', dimensions=None):
    """Send custom metric to CloudWatch"""
    try:
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Namespace': 'SmartExpenseMonitor'
        }
        if dimensions:
            metric_data['Dimensions'] = dimensions
        
        cloudwatch.put_metric_data(
            Namespace='SmartExpenseMonitor',
            MetricData=[metric_data]
        )
        print(f"Published metric: {metric_name} = {value} {unit}")
    except Exception as e:
        print(f"Error publishing metric {metric_name}: {str(e)}")

EXPENSES_TABLE = os.environ.get('EXPENSES_TABLE_NAME')
RECEIPTS_TABLE = os.environ.get('RECEIPTS_TABLE_NAME')
USER_SETTINGS_TABLE = os.environ.get('USER_SETTINGS_TABLE_NAME')
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
ENABLE_TEXTRACT = os.environ.get('ENABLE_TEXTRACT', 'false').lower() == 'true'

expenses_table = dynamodb.Table(EXPENSES_TABLE)
receipts_table = dynamodb.Table(RECEIPTS_TABLE)
user_settings_table = dynamodb.Table(USER_SETTINGS_TABLE) if USER_SETTINGS_TABLE else None


def lambda_handler(event, context):
    """Main handler - routes to S3 or API Gateway handlers"""
    print(f"Received event: {json.dumps(event)}")
    
    if 'Records' in event:
        return handle_s3_event(event)
    
    if 'httpMethod' in event or 'requestContext' in event:
        return handle_api_event(event)
    
    return {
        'statusCode': 400,
        'body': json.dumps({'message': 'Invalid event type'})
    }


def handle_s3_event(event):
    """Handle receipt upload from S3"""
    try:
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            print(f"Processing receipt: s3://{bucket}/{key}")
            
            userId = extract_user_id_from_key(key)
            if not userId:
                print(f"Warning: Could not extract userId from key: {key}")
                continue
            
            print(f"Extracted userId: {userId}")
            
            extracted_text = ""
            if ENABLE_TEXTRACT:
                extracted_text = extract_text_from_receipt(bucket, key)
            else:
                print("Textract disabled, skipping extraction")
            
            receipt_data = parse_receipt_data(extracted_text, key, userId)
            save_receipt_metadata(key, receipt_data, userId)
            
            if receipt_data.get('expense_data'):
                save_expense(receipt_data['expense_data'], userId)
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
    """Extract userId from S3 key (format: users/{userId}/uploads/{filename})"""
    try:
        parts = key.split('/')
        if len(parts) >= 3 and parts[0] == 'users':
            return parts[1]
        print(f"Invalid key format: {key}")
        return None
    except Exception as e:
        print(f"Error extracting userId from key {key}: {str(e)}")
        return None


def handle_api_event(event):
    """Route API Gateway requests to appropriate handlers"""
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    resource = event.get('resource', '')
    path_parameters = event.get('pathParameters') or {}
    
    print(f"API Event - Method: {http_method}, Path: {path}, Resource: {resource}")
    
    if http_method == 'GET':
        if '/expenses' in path or '/expenses' in resource:
            if path_parameters.get('id'):
                return get_expense(event, path_parameters['id'])
            return get_expenses(event)
        elif '/settings' in path or '/settings' in resource:
            return get_user_settings(event)
    
    elif http_method == 'POST':
        if '/receipts' in path or '/receipts' in resource or resource == '/receipts':
            return upload_receipt(event)
    
    elif http_method == 'PUT':
        if '/expenses' in path or '/expenses' in resource:
            if path_parameters.get('id'):
                return update_expense(event, path_parameters['id'])
        elif '/settings' in path or '/settings' in resource:
            return update_user_settings(event)
    
    print(f"No handler found for {http_method} {path}")
    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'message': 'Not found'})
    }


def extract_text_from_receipt(bucket, key):
    """Use Textract to extract text from receipt image"""
    start_time = time.time()
    
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
        
        text_blocks = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block.get('Text', ''))
        
        extracted_text = '\n'.join(text_blocks)
        processing_time = (time.time() - start_time) * 1000
        
        print(f"Extracted {len(extracted_text)} chars, {len(text_blocks)} lines in {processing_time:.2f}ms")
        
        try:
            publish_metric('TextractProcessingTime', processing_time, 'Milliseconds')
        except Exception as e:
            print(f"Error publishing Textract metric: {str(e)}")
        
        if extracted_text:
            preview = extracted_text[:200].replace('\n', ' ')
            print(f"Preview: {preview}...")
        else:
            print("Warning: No text extracted")
        
        return extracted_text
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return ""


def parse_receipt_data(text, key, userId):
    """Parse store name, amount, date, category, and items from receipt text"""
    receipt_id = str(uuid.uuid4())
    upload_date = datetime.utcnow().isoformat()
    
    text_upper = text.upper() if text else ""
    text_lower = text.lower() if text else ""
    lines = text.split('\n') if text else []
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
    
    for line in lines[:10]:
        line_lower = line.lower().strip()
        for store_key, store_value in common_stores.items():
            if store_key in line_lower:
                store_name = store_value
                print(f"Found store: {store_name}")
                break
        if store_name != 'Unknown Store':
            break
    
    amount = Decimal('0.0')
    total_match = re.search(
        r'TOTAL[^\d\n]*\$?\s*(\d+\.\d{2})',
        text_upper,
        re.IGNORECASE
    )
    if not total_match:
        total_match = re.search(
            r'TOTAL[^\d\n]*\n\s*\$?\s*(\d+\.\d{2})',
            text_upper,
            re.IGNORECASE
        )

    if total_match:
        amount = Decimal(total_match.group(1))
        print(f"Found amount: ${amount}")
    else:
        amount_patterns = [
            r'total\s*:?\s*\$?\s*(\d+\.\d{2})',
            r'total\s+amount\s*:?\s*\$?\s*(\d+\.\d{2})',
            r'amount\s+due\s*:?\s*\$?\s*(\d+\.\d{2})',
            r'grand\s+total\s*:?\s*\$?\s*(\d+\.\d{2})',
            r'balance\s+due\s*:?\s*\$?\s*(\d+\.\d{2})',
            r'\$\s*(\d+\.\d{2})\s*$',
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
                        print(f"Found amount (fallback): ${amount}")
                        break
                    except (ValueError, IndexError):
                        continue
            if amount > 0:
                break

    if amount == 0 and text_upper:
        dollar_amounts = []
        for line in lines:
            up = line.upper()
            if any(k in up for k in ['DISCOUNT', 'CHANGE', 'CASH', 'PAYMENT', 'TAX', 'SUBTOTAL']):
                continue
            dollar_amounts.extend(re.findall(r'\$?\s*(\d+\.\d{2})', up))

        if dollar_amounts:
            try:
                amounts = [Decimal(amt) for amt in dollar_amounts]
                amount = max(amounts)
                print(f"Found largest amount: ${amount}")
            except (ValueError, TypeError):
                pass
    
    receipt_date = upload_date
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})',
    ]
    
    for line in lines[:20]:
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
    
    items = extract_items_from_receipt(lines, text_upper, amount)
    
    print(f"Parsed receipt - Store: {store_name}, Amount: ${amount}, Date: {receipt_date}, Category: {category}, Items: {len(items)}")
    
    return {
        'receiptId': receipt_id,
        'userId': userId,
        's3Key': key,
        'uploadDate': upload_date,
        'extractedText': text[:500] if text else '',
        'expense_data': {
            'expenseId': receipt_id,
            'userId': userId,
            'amount': amount,
            'storeName': store_name,
            'date': receipt_date,
            'category': category,
            'items': items
        }
    }


def extract_items_from_receipt(lines, text_upper, total_amount):
    """Extract item name, price, quantity from receipt lines"""
    items = []
    
    if not lines:
        return items
    skip_keywords = [
        'TOTAL', 'SUBTOTAL', 'TAX', 'AMOUNT', 'DUE', 'CHANGE', 'CASH', 'CARD',
        'THANK', 'RECEIPT', 'STORE', 'ADDRESS', 'PHONE', 'DATE', 'TIME',
        'ITEM', 'DESCRIPTION', 'PRICE', 'QTY', 'QUANTITY'
    ]
    
    item_start_idx = 0
    for i, line in enumerate(lines[:15]):
        line_upper = line.upper().strip()
        if any(keyword in line_upper for keyword in ['ITEM', 'DESCRIPTION', 'PRODUCT']):
            item_start_idx = i + 1
            break
        if i > 5 and '$' in line or re.search(r'\d+\.\d{2}', line):
            item_start_idx = i
            break
    
    item_end_idx = len(lines)
    for i in range(len(lines) - 1, max(0, len(lines) - 20), -1):
        line_upper = lines[i].upper().strip()
        if any(keyword in line_upper for keyword in ['TOTAL', 'SUBTOTAL', 'TAX', 'AMOUNT DUE']):
            item_end_idx = i
            break
    
    item_lines = lines[item_start_idx:item_end_idx]
    
    for line in item_lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        line_upper = line.upper()
        if any(keyword in line_upper for keyword in skip_keywords):
            continue
        
        price_patterns = [
            r'\$?\s*(\d+\.\d{2})\s*$',
            r'\$\s*(\d+\.\d{2})',
            r'(\d+\.\d{2})\s*$',
        ]
        
        item_price = None
        item_name = None
        
        for pattern in price_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    price = Decimal(match.group(1))
                    if 0.01 <= price <= 1000:
                        item_price = price
                        item_name = line[:match.start()].strip()
                        break
                except (ValueError, IndexError):
                    continue
        
        if item_price and item_name:
            item_name = re.sub(r'\s+', ' ', item_name).strip()
            
            if len(item_name) < 2 or re.match(r'^\d+[\.\-\/]', item_name):
                continue
            
            quantity = Decimal('1.0')
            qty_patterns = [
                r'^(\d+)\s*x\s+',
                r'^(\d+)\s*@\s*',
                r'^(\d+)\s+',
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
    
    if items:
        seen = set()
        unique_items = []
        for item in items:
            key = (item['name'].lower(), float(item['price']))
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        items = unique_items
        
        items_total = sum(item['subtotal'] for item in items)
        if total_amount > 0:
            if abs(float(items_total) - float(total_amount)) / float(total_amount) > 0.1:
                print(f"Warning: Items total (${items_total}) doesn't match receipt total (${total_amount})")
        
        print(f"Extracted {len(items)} items")
        for item in items[:5]:
            print(f"  - {item['name']}: ${item['price']} x {item['quantity']} = ${item['subtotal']}")
    else:
        print("No items extracted")
    
    return items


def save_receipt_metadata(key, receipt_data, userId):
    """Save receipt metadata to receipts table"""
    item = {
        'receiptId': receipt_data['receiptId'],
        'userId': userId,
        's3Key': key,
        'uploadDate': receipt_data['uploadDate'],
        'extractedText': receipt_data.get('extractedText', ''),
        'status': 'processed'
    }
    
    receipts_table.put_item(Item=item)
    print(f"Saved receipt metadata for user {userId}: {receipt_data['receiptId']}")


def trigger_expense_check(userId):
    """Invoke expense notifier lambda asynchronously"""
    try:
        lambda_client = boto3.client('lambda')
        notifier_function_name = os.environ.get('NOTIFIER_FUNCTION_NAME', '')
        
        if not notifier_function_name:
            print("NOTIFIER_FUNCTION_NAME not set, skipping expense check")
            return
        
        lambda_client.invoke(
            FunctionName=notifier_function_name,
            InvocationType='Event',
            Payload=json.dumps({
                'source': 'receipt_processor',
                'userId': userId,
                'trigger': 'receipt_upload'
            })
        )
        print(f"Triggered expense check for user {userId}")
    except Exception as e:
        print(f"Error triggering expense check: {str(e)}")


def save_expense(expense_data, userId):
    """Save expense to expenses table and publish metrics"""
    expense_data['userId'] = userId
    expense_data['expenseId'] = expense_data.get('expenseId', str(uuid.uuid4()))
    expense_data['createdAt'] = datetime.utcnow().isoformat()
    
    if 'amount' in expense_data and isinstance(expense_data['amount'], float):
        expense_data['amount'] = Decimal(str(expense_data['amount']))
    elif 'amount' in expense_data and not isinstance(expense_data['amount'], Decimal):
        try:
            expense_data['amount'] = Decimal(str(expense_data['amount']))
        except (ValueError, TypeError):
            expense_data['amount'] = Decimal('0.0')
    
    expenses_table.put_item(Item=expense_data)
    print(f"Saved expense for user {userId}: {expense_data['expenseId']}")
    
    try:
        amount_value = float(expense_data.get('amount', 0))
        publish_metric('ExpensesProcessed', 1, 'Count')
        publish_metric('TotalExpenseAmount', amount_value, 'None')
        
        category = expense_data.get('category', 'Other')
        publish_metric('ExpenseByCategory', amount_value, 'None', [
            {'Name': 'Category', 'Value': category}
        ])
        
        expense_date = expense_data.get('date', datetime.utcnow().isoformat())
        if expense_date:
            try:
                date_obj = datetime.fromisoformat(expense_date.replace('Z', '+00:00'))
                month_key = date_obj.strftime('%Y-%m')
                publish_metric('MonthlySpending', amount_value, 'None', [
                    {'Name': 'Month', 'Value': month_key},
                    {'Name': 'UserId', 'Value': userId}
                ])
            except (ValueError, AttributeError):
                pass
    except Exception as e:
        print(f"Error publishing metrics: {str(e)}")


def get_expenses(event):
    """Fetch all expenses for authenticated user"""
    try:
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        userId = claims.get('sub') or claims.get('cognito:username')
        
        if not userId:
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
        
        items = response.get('Items', [])
        for item in items:
            if 'amount' in item and isinstance(item['amount'], Decimal):
                item['amount'] = float(item['amount'])
            
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
    """Get single expense by ID"""
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
        
        item = response['Item']
        if 'amount' in item and isinstance(item['amount'], Decimal):
            item['amount'] = float(item['amount'])
        
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
    """Update expense category and/or items"""
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
        
        body = json.loads(event.get('body', '{}'))
        new_category = body.get('category')
        new_items = body.get('items')
        
        if not new_category and new_items is None:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Either category or items must be provided'})
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
        
        expense = response['Item']
        update_expressions = []
        expression_attribute_names = {}
        expression_attribute_values = {}
        
        if new_category:
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
        
        if new_items is not None:
            if not isinstance(new_items, list):
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': 'Items must be an array'})
                }
            
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
            
            update_expressions.append('#items = :items')
            update_expressions.append('#amount = :amount')
            expression_attribute_names['#items'] = 'items'
            expression_attribute_names['#amount'] = 'amount'
            expression_attribute_values[':items'] = processed_items
            expression_attribute_values[':amount'] = total_amount
        
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
        
        updated_expense = expenses_table.get_item(
            Key={
                'userId': userId,
                'expenseId': expenseId
            }
        )['Item']
        
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
    """Generate presigned URL for S3 receipt upload"""
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
        
        if not fileName.startswith(f'users/{userId}/'):
            fileName = f'users/{userId}/uploads/{fileName.split("/")[-1]}'
        
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': fileName,
                'ContentType': fileType
            },
            ExpiresIn=300
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
    """Get user settings from settings table"""
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
    """Update user settings (threshold and email notifications)"""
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
        
        threshold_decimal = Decimal(str(monthly_threshold))
        print(f"Updating settings for user: {userId}, threshold: ${threshold_decimal}")
        user_email = claims.get('email', '')
        
        settings_item = {
            'userId': userId,
            'monthlyThreshold': threshold_decimal,
            'emailNotifications': email_notifications,
            'email': user_email,
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        user_settings_table.put_item(Item=settings_item)
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

