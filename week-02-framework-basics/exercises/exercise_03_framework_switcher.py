"""
Exercise 3: Framework Switcher
================================
Difficulty: Intermediate | Time: 2.5 hours

Task:
Build an agent system where the SAME tools and SAME query can run
on either LangGraph or ADK, switchable via a parameter. Then compare
the outputs from both frameworks.

This teaches you to think about tools as framework-agnostic logic.

Instructions:
1. Complete the shared tool functions (plain Python — no decorators)
2. Implement build_langgraph_agent() that wraps tools for LangGraph
3. Implement build_adk_agent() that uses tools with ADK
4. Implement run_with_framework() that dispatches to the right framework
5. Implement compare_frameworks() that runs both and prints results
6. Test with the queries below

Hints:
- Write tool logic ONCE as plain functions
- For LangGraph: use @tool decorator when wrapping
- For ADK: pass plain functions directly
- Use time.time() to measure execution time
- Look at example_05_framework_comparison.py for the pattern

Run: python week-02-framework-basics/exercises/exercise_03_framework_switcher.py
"""

import asyncio
import os
import time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv("config/.env")
load_dotenv()


# ══════════════════════════════════════════════════════════════
# Step 1: Shared tool logic (framework-agnostic)
# ══════════════════════════════════════════════════════════════
# Write the core logic here. These functions will be wrapped
# differently for each framework.

def calculate_logic(expression: str) -> str:
    """Evaluate a math expression safely.

    Args:
        expression: A math expression like '15 * 7' or '2 ** 10'

    Returns:
        A string with the result, e.g., '15 * 7 = 105'
    """
    # TODO: Implement safe math evaluation
    # 1. Validate that only safe characters are used (digits, operators, spaces, dots, parens)
    # 2. Use eval() to compute
    # 3. Return formatted result string
    # 4. Handle errors gracefully (return error message)
    if not all(c in "0123456789+-*/(). " for c in expression):
        return "Invalid characters in expression. Only digits, +, -, *, /, parentheses, dots, spaces, and operators are allowed."
    try:
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}" 


def reverse_text_logic(text: str) -> str:
    """Reverse a string.

    Args:
        text: The text to reverse

    Returns:
        The reversed text
    """
    return text[::-1]


# ══════════════════════════════════════════════════════════════
# Step 2: Build LangGraph agent
# ══════════════════════════════════════════════════════════════

def build_langgraph_agent():
    """Build a LangGraph agent using the shared tools.

    Returns:
        A compiled LangGraph app ready to invoke.
    """
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage
    from langgraph.graph import StateGraph, END, START
    from langgraph.prebuilt import ToolNode
    from typing import TypedDict, Annotated
    from langgraph.graph import add_messages

    # TODO: Wrap shared functions with @tool decorator
    @tool
    def calculate(expression: str) -> str:
        """Evaluate a math expression. Example: '15 * 7'"""
        return calculate_logic(expression)

    @tool
    def reverse_text(text: str) -> str:
        """Reverse a string."""
        return reverse_text_logic(text)

    # TODO: Set up LLM with provider flexibility (groq/openai)
    # TODO: Bind tools to LLM
    # TODO: Define AgentState (TypedDict with messages)
    # TODO: Define agent_node and should_continue functions
    # TODO: Build StateGraph with agent → tools → agent loop
    # TODO: Return compiled graph
    from langchain_openrouter import ChatOpenRouter
    llm = ChatOpenRouter(model=os.getenv("OPEN_ROUTER_MODEL", "gpt-4o-mini"))
    tools = [calculate, reverse_text]

    llm_with_tools = llm.bind_tools(tools)

    class AgentState(TypedDict):
        messages: Annotated[list, add_messages]
        tool_call_count: int

    def agent_node(state):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response], "tool_call_count": state.get("tool_call_count", 0) + 1}
    
    def should_continue(state):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"
    
    graph = StateGraph(AgentState)
    graph.add_node("agent_node", agent_node)
    graph.add_node("tool_node", ToolNode(tools))

    graph.add_edge(START, "agent_node")
    graph.add_conditional_edges("agent_node", should_continue, {"tools": "tool_node", "end": END})
    graph.add_edge("tool_node", "agent_node")
    return graph.compile()
# ══════════════════════════════════════════════════════════════
# Step 3: Build ADK agent
# ══════════════════════════════════════════════════════════════
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
def build_adk_agent():
    """Build an ADK agent using the shared tools.

    Returns:
        Tuple of (runner, session_service)
    """

    # TODO: Create ADK-compatible tool functions
    # These can call the shared logic directly:
    def calculate(expression: str) -> str:
        """Evaluate a math expression. Example: '15 * 7'"""
        return calculate_logic(expression)
    
    def reverse_text(text: str) -> str:
        """Reverse a string."""
        return reverse_text_logic(text)

    # TODO: Create LlmAgent with tools
    # TODO: Create InMemorySessionService and Runner
    # TODO: Return (runner, session_service)
    llm_model = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
    agent = LlmAgent(
        name="multi_tool_agent",
        model=llm_model,        
        instruction=f""" You are a helpful assistant that can perform calculations and reverse text.
Use the following tools to answer user queries:
1. calculate(expression): Evaluate math expressions. Use for queries like "What is 25 * 4?" or "Calculate (100 - 32) * 5 / 9".
2. reverse_text(text): Reverse a string. Use for queries like "Reverse the word 'framework'".
Always choose the most appropriate tool based on the user's query. If the query involves math, use calculate(). If it involves text manipulation, use reverse_text(). """,
        tools=[calculate, reverse_text],
    )   

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="multi_tool_app",
        session_service=session_service,
    )
    return runner, session_service


async def ask_agent(runner, session_service, session_id, query):
    """Ask the ADK agent a question and return the response."""
    async for event in runner.run_async(
        user_id="student",
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=query)]),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            return event.content.parts[0].text
    return "No response from agent."


# ══════════════════════════════════════════════════════════════
# Step 4: Run with either framework
# ══════════════════════════════════════════════════════════════

def run_with_framework(framework: str, query: str) -> dict:
    """Run a query using the specified framework.

    Args:
        framework: "langgraph" or "adk"
        query: The user's question

    Returns:
        Dict with keys: "result" (str), "time_seconds" (float), "framework" (str)
    """
    # TODO: Implement this dispatcher
    # 1. If framework == "langgraph":
    #    - Call build_langgraph_agent()
    #    - Invoke with the query
    #    - Time the execution
    #    - Return result dict
    #
    # 2. If framework == "adk":
    #    - Call build_adk_agent()
    #    - Create session, run query async
    #    - Time the execution
    #    - Return result dict
    #
    # 3. Handle errors — return error message in result dict
    if framework == "langgraph":
        agent = build_langgraph_agent()
        start_time = time.time()
        result = agent.invoke({"messages": [HumanMessage(content=query)]})
        end_time = time.time()
        final_message = result["messages"][-1]
        return {"result": final_message.content, "time_seconds": end_time - start_time, "framework": "langgraph"}
    elif framework == "adk":    
        runner, session_service = build_adk_agent()
        session_id = "test_session"
        start_time = time.time()

        async def _run():
            session = await session_service.create_session(
                app_name="multi_tool_app", user_id="student"
            )
            return await ask_agent(runner, session_service, session.id, query)
    
        result = asyncio.run(_run())
        end_time = time.time()
        return {"result": result, "time_seconds": end_time - start_time, "framework": "adk"}
    else:
        return {"result": f"Unknown framework: {framework}", "time_seconds": 0, "framework": framework} 


# ══════════════════════════════════════════════════════════════
# Step 5: Compare both frameworks
# ══════════════════════════════════════════════════════════════

def compare_frameworks(query: str):
    """Run the same query on both frameworks and print comparison.

    Args:
        query: The question to ask both frameworks
    """
    # TODO: Implement comparison
    # 1. Run with LangGraph: run_with_framework("langgraph", query)
    # 2. Run with ADK: run_with_framework("adk", query)
    # 3. Print both results side by side
    # 4. Print execution times
    # 5. Note any differences in the answers
    langgraph_result = run_with_framework("langgraph", query)
    adk_result = run_with_framework("adk", query)
    print(f"Query: {query}\n")
    print(f"LangGraph Result: {langgraph_result['result']} (Time: {langgraph_result['time_seconds']:.2f} seconds)")
    print(f"ADK Result: {adk_result['result']} (Time: {adk_result['time_seconds']:.2f} seconds)")
    if langgraph_result['result'] != adk_result['result']:
        print("\nNote: The results differ between frameworks!")
    else:        
        print("\nNote: Both frameworks returned the same result.") 


# ══════════════════════════════════════════════════════════════
# Test your implementation
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Exercise 3: Framework Switcher")
    print("=" * 50)

    # Test 1: Simple calculation
    print("\nTest 1: What is 15 * 7?")
    compare_frameworks("What is 15 * 7?")

    # Test 2: String operation
    print("\nTest 2: Reverse the word 'framework'")
    compare_frameworks("Reverse the word 'framework'")

    # Test 3: Multi-step (requires chaining)
    print("\nTest 3: Calculate 2 ** 10 and then reverse that number")
    compare_frameworks("Calculate 2 to the power of 10, then reverse that number as a string")

    print("\n(Uncomment the test code above after implementing!)")
