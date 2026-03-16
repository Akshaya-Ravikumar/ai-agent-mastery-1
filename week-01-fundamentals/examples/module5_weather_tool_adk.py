"""
Module 5: Basic Tool Integration — ADK Weather Agent
======================================================
Builds a tool-using agent with Google ADK that can:
  - Fetch weather for any city (via wttr.in free API)
  - Get current time in any timezone

ADK tools are plain Python functions — no decorators needed.
ADK handles the tool-calling loop internally.

Requires: GOOGLE_API_KEY in your environment.

Run: python week-01-fundamentals/examples/module5_weather_tool_adk.py
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv("config/.env")
load_dotenv()

import requests
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# ── Step 1: Define tools as plain Python functions (no decorators) ──

def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Primary: Open-Meteo (free, no key, reliable)
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
            timeout=10,
        ).json()
        if geo.get("results"):
            loc = geo["results"][0]
            weather = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": loc["latitude"], "longitude": loc["longitude"], "current_weather": True},
                timeout=10,
            ).json()
            cw = weather["current_weather"]
            return f"Weather in {loc['name']}: {cw['temperature']}°C, wind {cw['windspeed']} km/h"
    except Exception:
        pass

    # Fallback: wttr.in (can be slow/unreliable)
    try:
        response = requests.get(
            f"https://wttr.in/{city}?format=%t+%C",
            timeout=5,
            headers={"User-Agent": "curl/7.68.0"},
        )
        if response.status_code == 200 and "Unknown" not in response.text:
            return f"Weather in {city}: {response.text.strip()}"
    except Exception:
        pass

    return f"Could not fetch weather for {city} (all sources unavailable)"


def get_time(timezone: str) -> str:
    """Get the current time for a timezone. Use IANA format like America/New_York, Asia/Tokyo, Europe/London."""
    from datetime import datetime
    import pytz

    try:
        tz = pytz.timezone(timezone)
        return f"Current time in {timezone}: {datetime.now(tz).strftime('%H:%M:%S')}"
    except Exception:
        return f"Invalid timezone: {timezone}"


# ── Step 2: Create the agent with tools (ADK wires them automatically) ──

weather_agent = LlmAgent(
    name="weather_agent",
    model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
    instruction="""You are a helpful weather and time assistant.
    Use the get_weather tool to check weather and get_time
    tool to check the current time in any timezone.""",
    tools=[get_weather, get_time],
)

# ── Step 3: Run it using Runner ──────────────────

session_service = InMemorySessionService()
runner = Runner(
    agent=weather_agent,
    app_name="weather_app",
    session_service=session_service,
)


async def run_weather_query():
    session = await session_service.create_session(
        app_name="weather_app", user_id="user1"
    )
    query = "What's the weather in London and time in Tokyo?"
    print(f"Query: {query}\n")

    async for event in runner.run_async(
        user_id="user1",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=query)]),
    ):
        if event.is_final_response():
            print(f"Agent: {event.content.parts[0].text}")


if __name__ == "__main__":
    print("Weather Tool Agent (ADK + Gemini)")
    print("=" * 50)
    asyncio.run(run_weather_query())
