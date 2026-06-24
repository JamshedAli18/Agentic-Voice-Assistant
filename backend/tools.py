# backend/tools.py

import math
import re
import requests
from langchain_core.tools import tool
from serpapi import GoogleSearch
from tavily import TavilyClient
from config import get_settings

settings = get_settings()


def search_with_tavily(query: str) -> str:
    """Search using Tavily API."""
    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = client.search(query, max_results=3, include_images=False)
        
        if response.get("results"):
            snippets = [
                f"{r.get('title', '')}: {r.get('content', '')}"
                for r in response["results"]
                if r.get("content")
            ]
            return "\n\n".join(snippets) if snippets else None
        return None
    except Exception as e:
        print(f"Tavily search failed: {e}")
        return None


def search_with_serpapi(query: str) -> str:
    """Search using SerpAPI."""
    try:
        search = GoogleSearch({
            "q": query,
            "api_key": settings.SERPAPI_API_KEY,
            "num": 3,
        })
        results = search.get_dict()

        # Try answer box first
        if results.get("answer_box"):
            box = results["answer_box"]
            if box.get("answer"):
                return box["answer"]
            if box.get("snippet"):
                return box["snippet"]

        # Try knowledge graph
        if results.get("knowledge_graph", {}).get("description"):
            return results["knowledge_graph"]["description"]

        # Fall back to organic results
        organic = results.get("organic_results", [])
        if organic:
            snippets = [
                f"{r.get('title', '')}: {r.get('snippet', '')}"
                for r in organic[:3]
                if r.get("snippet")
            ]
            return "\n\n".join(snippets) if snippets else None
        return None
    except Exception as e:
        print(f"SerpAPI search failed: {e}")
        return None


@tool
def search_web(query: str) -> str:
    """Search the web for real-time or current information using Tavily with SerpAPI as fallback."""
    # Try Tavily first (usually better for latest news)
    result = search_with_tavily(query)
    if result:
        return result
    
    # Fall back to SerpAPI
    result = search_with_serpapi(query)
    if result:
        return result
    
    return "No results found."


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression. Example: sqrt(144), 2**10, sin(pi/2)."""
    try:
        allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("_")
        }
        allowed_names.update({"abs": abs, "round": round})
        sanitized = re.sub(r"[^0-9+\-*/().,\s_a-zA-Z]", "", expression)
        result = eval(sanitized, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"


@tool
def get_weather(location: str) -> str:
    """Get current weather for a city or location."""
    try:
        # Use SerpAPI weather search instead of open-meteo
        search = GoogleSearch({
            "q": f"weather in {location}",
            "api_key": settings.SERPAPI_API_KEY,
        })
        results = search.get_dict()

        # SerpAPI returns a weather result block
        weather = results.get("answer_box") or results.get("weather_result")

        if weather:
            temp = weather.get("temperature", "")
            unit = weather.get("unit", "F")
            condition = weather.get("weather", weather.get("description", ""))
            humidity = weather.get("humidity", "")
            wind = weather.get("wind", "")

            parts = [f"Weather in {location}:"]
            if condition: parts.append(condition)
            if temp: parts.append(f"{temp}°{unit}")
            if humidity: parts.append(f"Humidity: {humidity}")
            if wind: parts.append(f"Wind: {wind}")

            return " ".join(parts)

        # Fallback to snippet
        organic = results.get("organic_results", [])
        if organic and organic[0].get("snippet"):
            return organic[0]["snippet"]

        return f"Could not get weather for {location}."

    except Exception as e:
        return f"Weather lookup failed: {str(e)}"


TOOLS = [search_web, calculator, get_weather]