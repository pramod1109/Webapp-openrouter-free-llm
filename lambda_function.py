import json
import os
import httpx
import re
import traceback
import database
import tools
import sam_agent
import prompts

def lambda_handler(event, context):
    # 1. Parse Input
    try:
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
    except:
        body = event
        
    user_prompt = body.get('prompt', '')
    session_id = body.get('session_id', 'default_user')
    
    print(f"DEBUG 1: Received prompt='{user_prompt}' session='{session_id}'")

    # 2. Logic: Should we use SAM.gov or News?
    naics_match = re.search(r'\b\d{6}\b', user_prompt)
    is_sam_request = any(word in user_prompt.lower() for word in ["naics", "sam", "contract", "solicitation"])
    
    print(f"DEBUG 2: is_sam_request={is_sam_request}, naics_match={naics_match}")
    
    sam_context = ""
    news_context = ""

    if is_sam_request:
        if naics_match:
            code = naics_match.group(0)
            print(f"DEBUG 3: Extracting SAM data for NAICS {code}")
            sam_context = sam_agent.get_sam_opportunities(code)
            print(f"DEBUG 4: SAM context returned='{sam_context[:200]}'")
            news_context = "System: Focusing exclusively on Government Contract data."
        else:
            sam_context = "User asked for SAM data but provided no NAICS code. Ask them for a 6-digit code."
            news_context = "System: Awaiting NAICS code."

    # 3. Get History from DynamoDB
    chat_history = database.get_chat_history(session_id)
    print(f"DEBUG 5: Chat history length={len(chat_history)}")

    # 4. Construct the Briefing using prompts.py
    full_prompt = prompts.get_sam_briefing(
        history=chat_history,
        sam_data=sam_context,
        user_input=user_prompt
    )
    print(f"DEBUG 6: Full prompt length={len(full_prompt)} chars")

    # 5. Call LLM
    api_key = os.environ.get("OPENROUTER_API_KEY")
    print(f"DEBUG 7: API key present={bool(api_key)}, prefix={api_key[:8] if api_key else 'NONE'}")
    MODELS = [
    "google/gemma-4-31b-it:free",
    "bytedance/seedance-2.0",
    "openrouter/elephant-alpha",
    "google/gemma-4-26b-a4b-it:free",
        ]
    ai_response = None

    for model in MODELS:
        try:
            print("DEBUG 8: About to call OpenRouter...")
            print(f"DEBUG: Trying model {model}")
        
            response = httpx.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-Title": "Fairfax AI Navigator"
                },
                json={
                "model": model,
                "messages": [{"role": "user", "content": full_prompt}],
                "temperature": 0.1,
                "max_tokens": 500
                },
            timeout=60.0
            )
        
            print(f"DEBUG 9: OpenRouter status code={response.status_code}")
        
            response_json = response.json()
            print(f"DEBUG: {model} status={response.status_code}")
            print(f"DEBUG 10: Raw OpenRouter response={json.dumps(response_json)[:500]}")
            if response_json.get("error"):
                print(f"DEBUG: {model} failed: {response_json['error']}")
                continue

            # Check for API-level errors
            if response_json.get("error"):
                print(f"DEBUG 11: OpenRouter returned error={response_json['error']}")
                ai_response = f"OpenRouter error: {response_json['error'].get('message', 'unknown')}"
            else:
                raw_content = response_json['choices'][0]['message']['content']
                print(f"DEBUG 11: raw_content type={type(raw_content)}, value={str(raw_content)[:300]}")
            
            if isinstance(raw_content, list):
                ai_response = " ".join(
                    block.get("text", "")
                    for block in raw_content
                    if block.get("type") == "text"
                ).strip()
            else:
                ai_response = raw_content.strip()

            if not ai_response:
                print("DEBUG 12: ai_response was empty after extraction")
                ai_response = "I processed your request but got an empty response."
                
            print(f"DEBUG 13: Final ai_response='{ai_response[:200]}'")

        except Exception as e:
            print(f"LLM Error Full Traceback: {traceback.format_exc()}")
            ai_response = f"Exception caught: {str(e)}"  # Temporarily show real error

    # 6. Save the Exchange
    database.save_chat_message(session_id, user_prompt, ai_response)

    # 7. Return to Frontend
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps({"response": ai_response})
    }