import boto3
from boto3.dynamodb.conditions import Key
import time

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
# Replace 'UserConversations' with your actual table name
table = dynamodb.Table('ChatHistory')

def get_chat_history(session_id, limit=10):
    try:
        response = table.query(
            KeyConditionExpression=Key('SessionId').eq(session_id),
            ScanIndexForward=False, 
            Limit=limit
        )
        items = response.get('Items', [])
        
        history_text = ""
        for item in reversed(items):
            # Safe retrieval: try 'user_msg', fallback to empty string
            user_msg = item.get('user_msg', '')
            ai_msg = item.get('ai_msg', '')
            
            # Only add to history if both parts exist
            if user_msg and ai_msg:
                history_text += f"User: {user_msg}\nAI: {ai_msg}\n"
                
        return history_text
    except Exception as e:
        # This print will show up in your CloudWatch logs
        print(f"DB Read Error Details: {str(e)}")
        return ""

def save_chat_message(session_id, user_msg, ai_msg):
    """Saves the current exchange to the database."""
    try:
        table.put_item(
            Item={
                'SessionId': session_id,
                'Timestamp': int(time.time()),
                'user_msg': user_msg,
                'ai_msg': ai_msg
            }
        )
    except Exception as e:
        print(f"DB Write Error: {e}")