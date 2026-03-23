"""
Exercise 2: Smart Summarizer
==============================
Difficulty: Beginner | Time: 2 hours

Task:
Build an LLM-powered text analyzer that returns structured output
with: summary, key_terms, and sentiment.

Instructions:
1. Set up your OpenAI API key
2. Create a Pydantic model for the output schema
3. Use .with_structured_output() for guaranteed schema compliance
4. Test with at least 2 different paragraphs
5. Bonus: Add Phoenix tracing to view the LLM call

Run: python exercise_02_smart_summarizer.py
"""

from pydantic import BaseModel, Field
from typing import List, Literal

from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import HumanMessage, SystemMessage

class TextAnalysis(BaseModel):
    """Define the output schema here."""
    # TODO: Add fields for summary, key_terms, and sentiment
    summary: str = Field(description="A 1-2 sentence summary.")
    key_terms: List[str] = Field(description ="List of important key words")
    sentiment: Literal ["positive", "negative", "neutral"] = Field(description = "User Sentiments that can be either positive, negative or neutral")


model = ChatOpenRouter(
        model="openai/gpt-4o-mini",
        temperature="0"
    )
structured_model = model.with_structured_output(TextAnalysis, method="json_schema")

def analyze_text(text: str) -> TextAnalysis:
    """Analyze text and return structured insights.

    Args:
        text: The text to analyze

    Returns:
        TextAnalysis with summary, key_terms, and sentiment
    """
    # TODO: Implement this function
    # 1. Initialize ChatOpenAI with gpt-4o-mini
    # 2. Use .with_structured_output(TextAnalysis)
    # 3. Create a clear prompt asking for summary, key terms, and sentiment
    # 4. Return the structured result

    if not text or not text.strip():
        raise ValueError("Input text cannot be empty.")

    messages = [
        SystemMessage(content="You are an expert text analyst."),
        HumanMessage(content=f"""Analyze the following text. Provide:
        1. A 1-2 sentence summary
        2. Key terms as a list
        3. Overall sentiment (positive, negative, or neutral)

        Text: {text}
        """)
    ]
    
    try:
        return structured_model.invoke(messages)
    except Exception as e:
        print(f"LLM call failed: {e}")
        raise ValueError("LLM call failed")

if __name__ == "__main__":
    # Optional observability: traces each LLM call in Phoenix.

    sample = """
    AI agents represent a paradigm shift in software development.
    Unlike traditional programs, agents can reason about their
    environment, use tools autonomously, and improve through
    self-reflection. Companies like Klarna have deployed agents
    that handle millions of customer interactions.
    """

    print("Analyzing text...")
    result = analyze_text(sample)
    print(f"Summary: {result.summary}")
    print(f"Key Terms: {result.key_terms}")
    print(f"Sentiment: {result.sentiment}")
