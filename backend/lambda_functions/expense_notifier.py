import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
ses_client = boto3.client('ses')

# Get table names from environment variables
EXPENSES_TABLE = os.environ.get('EXPENSES_TABLE_NAME')
USER_SETTINGS_TABLE = os.environ.get('USER_SETTINGS_TABLE_NAME')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'shraym@proton.me')

expenses_table = dynamodb.Table(EXPENSES_TABLE)
user_settings_table = dynamodb.Table(USER_SETTINGS_TABLE) if USER_SETTINGS_TABLE else None


def lambda_handler(event, context):
    """
    Lambda handler for checking monthly expenses and sending notifications.
    Can be triggered by:
    1. EventBridge scheduled event (monthly check)
    2. API Gateway (manual trigger)
    3. Receipt processor (after expense is saved) - real-time check
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Handle EventBridge scheduled event
    if 'source' in event and event['source'] == 'aws.events':
        return check_all_users_expenses()
    
    # Handle API Gateway event (manual trigger)
    if 'httpMethod' in event or 'requestContext' in event:
        return handle_api_event(event)
    
    # Handle receipt processor trigger (real-time check after upload)
    if 'source' in event and event['source'] == 'receipt_processor':
        userId = event.get('userId')
        if userId:
            print(f"Real-time expense check triggered for user: {userId}")
            return check_single_user_expenses(userId)
    
    # Handle S3 event (legacy - for backward compatibility)
    if 'Records' in event:
        return handle_s3_event(event)
    
    return {
        'statusCode': 400,
        'body': json.dumps({'message': 'Invalid event type'})
    }


def check_all_users_expenses():
    """Check expenses for all users and send notifications"""
    try:
        if not user_settings_table:
            print("User settings table not configured")
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'User settings table not configured'})
            }
        
        # Scan all user settings
        response = user_settings_table.scan()
        users = response.get('Items', [])
        
        print(f"Checking expenses for {len(users)} users")
        
        notifications_sent = 0
        for user_setting in users:
            try:
                if check_and_notify_user(user_setting):
                    notifications_sent += 1
            except Exception as e:
                print(f"Error checking user {user_setting.get('userId')}: {str(e)}")
                continue
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Checked {len(users)} users, sent {notifications_sent} notifications'
            })
        }
    except Exception as e:
        print(f"Error checking all users: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }


def check_and_notify_user(user_setting):
    """Check if user's monthly expenses exceed threshold and send notification"""
    try:
        userId = user_setting.get('userId')
        threshold = user_setting.get('monthlyThreshold')
        email_notifications = user_setting.get('emailNotifications', True)
        user_email = user_setting.get('email')
        
        if not userId or not threshold or not email_notifications:
            return False
        
        if not user_email:
            print(f"No email found for user {userId}")
            return False
        
        # Get current month
        current_month = datetime.utcnow().strftime('%Y-%m')
        
        # Query expenses for current month using DateIndex GSI
        try:
            response = expenses_table.query(
                IndexName='DateIndex',
                KeyConditionExpression='userId = :userId AND begins_with(#date, :month)',
                ExpressionAttributeNames={
                    '#date': 'date'
                },
                ExpressionAttributeValues={
                    ':userId': userId,
                    ':month': current_month
                }
            )
        except Exception as e:
            # Fallback to scan if GSI query fails
            print(f"GSI query failed, using scan: {str(e)}")
            response = expenses_table.scan(
                FilterExpression='userId = :userId AND begins_with(#date, :month)',
                ExpressionAttributeNames={
                    '#date': 'date'
                },
                ExpressionAttributeValues={
                    ':userId': userId,
                    ':month': current_month
                }
            )
        
        expenses = response.get('Items', [])
        monthly_total = sum(float(exp.get('amount', 0)) for exp in expenses)
        threshold_float = float(threshold)
        
        print(f"User {userId}: Monthly total: ${monthly_total}, Threshold: ${threshold_float}")
        
        # Check if threshold is exceeded
        if monthly_total > threshold_float:
            # Send notification
            email_sent = send_notification_email(user_email, userId, monthly_total, threshold_float, current_month)
            if email_sent:
                print(f"✓ Notification email sent successfully to {user_email}")
                return True
            else:
                print(f"⚠️ Could not send notification email to {user_email} (likely unverified in SES)")
                return False
        
        return False
        
    except Exception as e:
        print(f"Error checking user expenses: {str(e)}")
        raise


def send_notification_email(user_email, userId, monthly_total, threshold, month):
    """Send email notification to user"""
    try:
        subject = f"Monthly Expense Alert - You've Exceeded Your Threshold"
        
        body_text = f"""
Hello,

This is an automated notification from Smart Expense Monitor.

Your monthly expenses for {month} have exceeded your set threshold.

Current Monthly Total: ${monthly_total:.2f}
Your Threshold: ${threshold:.2f}
Over Budget By: ${monthly_total - threshold:.2f}

Please review your expenses in the Smart Expense Monitor dashboard.

Thank you,
Smart Expense Monitor Team
        """
        
        body_html = f"""
<html>
<head></head>
<body>
  <h2>Monthly Expense Alert</h2>
  <p>Hello,</p>
  <p>This is an automated notification from Smart Expense Monitor.</p>
  <p>Your monthly expenses for <strong>{month}</strong> have exceeded your set threshold.</p>
  <table style="border-collapse: collapse; margin: 20px 0;">
    <tr>
      <td style="padding: 8px; border: 1px solid #ddd;"><strong>Current Monthly Total:</strong></td>
      <td style="padding: 8px; border: 1px solid #ddd; color: #d32f2f;">${monthly_total:.2f}</td>
    </tr>
    <tr>
      <td style="padding: 8px; border: 1px solid #ddd;"><strong>Your Threshold:</strong></td>
      <td style="padding: 8px; border: 1px solid #ddd;">${threshold:.2f}</td>
    </tr>
    <tr>
      <td style="padding: 8px; border: 1px solid #ddd;"><strong>Over Budget By:</strong></td>
      <td style="padding: 8px; border: 1px solid #ddd; color: #d32f2f;">${monthly_total - threshold:.2f}</td>
    </tr>
  </table>
  <p>Please review your expenses in the Smart Expense Monitor dashboard.</p>
  <p>Thank you,<br>Smart Expense Monitor Team</p>
</body>
</html>
        """
        
        response = ses_client.send_email(
            Source=FROM_EMAIL,
            Destination={
                'ToAddresses': [user_email]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body_text,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': body_html,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        print(f"Notification email sent to {user_email}. MessageId: {response['MessageId']}")
        return True
        
    except Exception as e:
        error_message = str(e)
        print(f"Error sending email to {user_email}: {error_message}")
        
        # Check if it's a verification error
        if "Email address is not verified" in error_message or "MessageRejected" in error_message:
            print(f"⚠️ SES Sandbox Mode: Email {user_email} is not verified in AWS SES.")
            print(f"   Please verify this email in AWS SES Console or request production access.")
            print(f"   See SES_EMAIL_VERIFICATION.md for instructions.")
            # Don't raise - just log the error so the function completes
            # The user will need to verify their email in SES
            return False
        
        # For other errors, raise to be handled by caller
        raise


def handle_api_event(event):
    """Handle API Gateway requests"""
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    
    if http_method == 'POST' and '/notifications/check' in path:
        # Manual trigger to check all users
        return check_all_users_expenses()
    
    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'message': 'Not found'})
    }


def handle_s3_event(event):
    """Handle S3 event - check expenses after new expense is saved"""
    try:
        # Extract userId from S3 key
        for record in event.get('Records', []):
            key = record['s3']['object']['key']
            # Key format: users/{userId}/uploads/{filename}
            if '/users/' in key:
                parts = key.split('/')
                if len(parts) >= 2:
                    userId = parts[1]
                    # Check this user's expenses
                    check_user_expenses_after_upload(userId)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Processed'})
        }
    except Exception as e:
        print(f"Error handling S3 event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }


def check_single_user_expenses(userId):
    """Check expenses for a single user and send notification if threshold exceeded"""
    try:
        if not user_settings_table:
            print("User settings table not configured")
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'User settings table not configured'})
            }
        
        # Get user settings
        response = user_settings_table.get_item(Key={'userId': userId})
        if 'Item' not in response:
            print(f"No settings found for user {userId}")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': f'No threshold set for user {userId}'})
            }
        
        user_setting = response['Item']
        notified = check_and_notify_user(user_setting)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Checked user {userId}',
                'notified': notified
            })
        }
        
    except Exception as e:
        print(f"Error checking expenses for user {userId}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }


def check_user_expenses_after_upload(userId):
    """Check user's expenses after a new receipt is uploaded (legacy function)"""
    try:
        if not user_settings_table:
            return
        
        # Get user settings
        response = user_settings_table.get_item(Key={'userId': userId})
        if 'Item' not in response:
            return
        
        user_setting = response['Item']
        check_and_notify_user(user_setting)
        
    except Exception as e:
        print(f"Error checking expenses after upload for user {userId}: {str(e)}")

