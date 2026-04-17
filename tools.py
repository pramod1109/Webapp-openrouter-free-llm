import os
from duckduckgo_search import DDGS

def get_2026_news(query):
    """
    Fetches the latest news. This is optimized for the 
    Artemis II splashdown and other April 2026 events.
    """
    try:
        with DDGS() as ddgs:
            # We convert the generator to a list and grab the top 3 results
            results = list(ddgs.news(query, max_results=3))
            
            if not results:
                return "No recent news found for this topic."
            
            # Formatting the news into a clean string for the LLM to read
            formatted_news = "RECENT NEWS UPDATES:\n"
            for r in results:
                formatted_news += f"- {r['title']}: {r['body']}\n"
            
            return formatted_news
    except Exception as e:
        print(f"Search Error: {e}")
        return "I'm currently unable to fetch live news, but I can still chat!"

def get_weather_update(location="Fairfax, VA"):
    """
    Optional: You can add more tools here later without 
    messing up your main code.
    """
    # Placeholder for a weather API call
    return f"The weather in {location} is typical for April."