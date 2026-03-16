"""
Module 5: Basic Tool Integration — LangGraph Weather Agent
============================================================
Builds a tool-using agent with LangGraph that can:
  - Fetch weather for any city (via wttr.in free API)
  - Get current time in any timezone

The LLM decides which tools to call based on the user's question.

Run: python week-01-fundamentals/examples/module5_weather_tool_langgraph.py
"""

import os
from dotenv import load_dotenv

load_dotenv("config/.env")
load_dotenv()

import requests
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated
from langgraph.graph import add_messages


# ── Step 1: Define tools ──────────────────────

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city using a free API."""
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


@tool
def get_time(timezone: str) -> str:
    """Get the current time for a timezone. Use IANA format like America/New_York, Asia/Tokyo, Europe/London."""
    from datetime import datetime
    import pytz

    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return f"Current time in {timezone}: {now.strftime('%H:%M:%S')}"
    except Exception:
        return f"Invalid timezone: {timezone}"


# ── Step 2: Create LLM with tools bound ──────

tools = [get_weather, get_time]

provider = os.getenv("LLM_PROVIDER", "groq").lower()
if provider == "groq":
    from langchain_groq import ChatGroq
    llm = ChatGroq(model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
else:
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

llm_with_tools = llm.bind_tools(tools)


# ── Step 3: Define state and nodes ───────────

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def agent_node(state):
    """LLM decides whether to call a tool or respond directly."""
    # Groq/Llama models can intermittently generate malformed tool calls,
    # causing a 400 tool_use_failed error. Retry up to 3 times.
    for attempt in range(3):
        try:
            response = llm_with_tools.invoke(state["messages"])
            return {"messages": [response]}
        except Exception as e:
            if "tool_use_failed" in str(e) and attempt < 2:
                continue
            raise


def should_continue(state):
    """Route to tools if the LLM made a tool call, otherwise end."""
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "end"


# ── Step 4: Build the graph ──────────────────

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))
graph.set_entry_point("agent")
graph.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "end": END},
)
graph.add_edge("tools", "agent")  # After tool runs, go back to agent

app = graph.compile()


# ── Step 5: Run it! ──────────────────────────

if __name__ == "__main__":
    print(f"Weather Tool Agent (provider: {provider})")
    print("=" * 50)

    queries = [
        "What's the weather in London?",
        "What's the current time in Asia/Tokyo?",
    ]

    for query in queries:
        print(f"Query: {query}")
        try:
            result = app.invoke({"messages": [HumanMessage(content=query)]})
            print(f"Agent: {result['messages'][-1].content}\n")
        except Exception as e:
            print(f"Agent: [Error] {type(e).__name__}: {e}\n")
