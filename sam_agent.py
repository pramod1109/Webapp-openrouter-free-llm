import httpx
import os
from datetime import datetime, timedelta

def get_sam_opportunities(naics_code):
    api_key = os.environ.get("SAM_GOV_API_KEY")
    # v2 endpoint requires the /prod/ path usually
    base_url = "https://api.sam.gov/prod/opportunities/v2/search"
    
    # 1. Generate Mandatory Dates (Last 90 days)
    today = datetime.now()
    three_months_ago = today - timedelta(days=90)
    
    posted_from = three_months_ago.strftime("%m/%d/%Y")
    posted_to = today.strftime("%m/%d/%Y")
    
    # 2. Setup Parameters based on the documentation you provided
    params = {
        "api_key": api_key,
        "ncode": naics_code,
        "postedFrom": posted_from,
        "postedTo": posted_to,
        "limit": 5,
        "ptype": "o,k" # Filters for 'Solicitation' and 'Combined Synopsis'
    }
    
    try:
        response = httpx.get(base_url, params=params, timeout=15.0)
        
        # If SAM.gov returns an error code
        if response.status_code != 200:
            return f"SAM.gov API Error: {response.status_code} - {response.text}"
            
        data = response.json()
        opps = data.get('opportunitiesData', [])
        
        if not opps:
            return f"No active opportunities found for NAICS {naics_code} since {posted_from}."
            
        # 3. Format for the "Thinking" LLM
        results = "LIVE SAM.GOV OPPORTUNITIES FOUND:\n"
        for opp in opps:
            results += (
                f"- TITLE: {opp.get('title')}\n"
                f"  AGENCY: {opp.get('fullParentPathName')}\n"
                f"  SET-ASIDE: {opp.get('typeOfSetAsideDescription', 'N/A')}\n"
                f"  DEADLINE: {opp.get('responseDate', 'Check link')}\n"
                f"  LINK: https://sam.gov/opp/{opp.get('noticeId')}/view\n\n"
            )
        return results

    except Exception as e:
        return f"System Error connecting to SAM: {str(e)}"