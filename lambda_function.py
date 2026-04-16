import json

def lambda_handler(event, context):
    # Log the event so you can see it in CloudWatch
    print(f"Received event: {json.dumps(event)}")
    
    try:
        body = json.loads(event.get("body", "{}"))
        prompt = body.get("prompt", "No prompt provided")
    except Exception as e:
        prompt = "Error parsing input"

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps({
            "response": f"You sent: {prompt}. Hello from the LLM!"
        })
    }