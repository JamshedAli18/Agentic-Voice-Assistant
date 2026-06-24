# backend/agent.py

from typing import TypedDict, Literal, Annotated
import operator

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END

from config import get_settings
from tools import TOOLS, search_web, calculator, get_weather

settings = get_settings()

MAIN_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"

# ── Tool map ──────────────────────────────────────────────────────────────────
TOOL_MAP = {
    "search_web": search_web,
    "calculator": calculator,
    "get_weather": get_weather,
}

# ── Prompts ───────────────────────────────────────────────────────────────────
CLASSIFIER_PROMPT = """You are a routing assistant. Classify the user's message into one of these categories:

- "search"     → asks about current events, news, latest scores, sports results, tournament winners, today's date, recent happenings, or any event after 2023
- "calculator" → needs math calculation or arithmetic
- "weather"    → asks about weather in any location
- "general"    → can be answered from general knowledge before 2023, no tools needed

IMPORTANT: If the query mentions years (2024, 2025, 2026, etc.) or asks "who won", "what happened", "latest", "recent", classify as "search".

Reply with ONLY one word: search, calculator, weather, or general.
No explanation. No punctuation. Just the single word."""

AGENT_PROMPT = """You are a helpful, concise voice assistant. Keep responses SHORT and NATURAL — 
you are speaking aloud, not writing text. Avoid bullet points, markdown, or long lists.
Answer directly in 1-3 sentences. Never mention tool names."""

AGENT_WITH_CONTEXT_PROMPT = """You are a helpful, concise voice assistant. Keep responses SHORT and NATURAL — 
you are speaking aloud, not writing text. Avoid bullet points, markdown, or long lists.
Answer directly in 1-3 sentences using the tool result provided. Never mention tool names."""


# ── Graph State ───────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    user_message: str
    history: list[BaseMessage]
    category: str
    tool_result: str
    final_response: str


# ── LLM instances ─────────────────────────────────────────────────────────────
def get_llm(model: str = MAIN_MODEL) -> ChatGroq:
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=model,
        temperature=0.2,
        max_tokens=512,
    )


# ── Node 1: Classifier ────────────────────────────────────────────────────────
async def classify_node(state: AgentState) -> AgentState:
    """Classify whether the question needs a tool or general answer."""
    llm = get_llm(FALLBACK_MODEL)  # small fast model for classification

    messages = [
        SystemMessage(content=CLASSIFIER_PROMPT),
        HumanMessage(content=state["user_message"]),
    ]

    try:
        response = await llm.ainvoke(messages)
        category = response.content.strip().lower()

        # Sanitize — only accept known categories
        if category not in ["search", "calculator", "weather", "general"]:
            category = "general"

        print(f"Classified as: {category}")
        return {**state, "category": category}

    except Exception as e:
        print(f"Classifier failed: {e}")
        return {**state, "category": "general"}


# ── Node 2: Tool executor ─────────────────────────────────────────────────────
async def tool_node(state: AgentState) -> AgentState:
    """Execute the appropriate tool based on category."""
    category = state["category"]
    user_message = state["user_message"]
    tool_result = ""

    try:
        if category == "search":
            # Extract search query using LLM
            llm = get_llm(FALLBACK_MODEL)
            query_messages = [
                SystemMessage(content="You are a search query extractor. Take the user's question and convert it into a concise web search query. Return ONLY the search query, nothing else. Do NOT include explanations or meta-commentary."),
                HumanMessage(content=user_message),
            ]
            query_response = await llm.ainvoke(query_messages)
            query = query_response.content.strip()
            print(f"Search query: {query}")
            tool_result = search_web.invoke({"query": query})

        elif category == "calculator":
            # Extract math expression using LLM
            llm = get_llm(FALLBACK_MODEL)
            expr_messages = [
                SystemMessage(content="Extract only the mathematical expression from the user message. Reply with ONLY the expression, nothing else. Example: sqrt(144), 25*48, 2**10"),
                HumanMessage(content=user_message),
            ]
            expr_response = await llm.ainvoke(expr_messages)
            expression = expr_response.content.strip()
            print(f"Math expression: {expression}")
            tool_result = calculator.invoke({"expression": expression})

        elif category == "weather":
            # Extract location using LLM
            llm = get_llm(FALLBACK_MODEL)
            loc_messages = [
                SystemMessage(content="Extract only the city or location name from the user message. Reply with ONLY the location name, nothing else."),
                HumanMessage(content=user_message),
            ]
            loc_response = await llm.ainvoke(loc_messages)
            location = loc_response.content.strip()
            print(f"Weather location: {location}")
            tool_result = get_weather.invoke({"location": location})

        print(f"Tool result: {tool_result}")
        return {**state, "tool_result": tool_result}

    except Exception as e:
        print(f"Tool execution failed: {e}")
        return {**state, "tool_result": "", "category": "general"}


# ── Node 3: General answer ────────────────────────────────────────────────────
async def general_node(state: AgentState) -> AgentState:
    """Answer directly from LLM knowledge, no tools."""
    llm = get_llm(MAIN_MODEL)

    messages = [
        SystemMessage(content=AGENT_PROMPT),
        *state["history"],
        HumanMessage(content=state["user_message"]),
    ]

    try:
        response = await llm.ainvoke(messages)
        return {**state, "final_response": response.content}

    except Exception as e:
        print(f"General node failed: {e}")
        # Fallback to small model
        llm = get_llm(FALLBACK_MODEL)
        response = await llm.ainvoke(messages)
        return {**state, "final_response": response.content}


# ── Node 4: Synthesize tool result into natural response ──────────────────────
async def synthesize_node(state: AgentState) -> AgentState:
    """Turn raw tool result into a natural voice response."""
    llm = get_llm(MAIN_MODEL)

    messages = [
        SystemMessage(content=AGENT_WITH_CONTEXT_PROMPT),
        *state["history"],
        HumanMessage(content=state["user_message"]),
        AIMessage(content=f"Tool result: {state['tool_result']}"),
        HumanMessage(content="Now give a natural, concise spoken response based on the tool result above."),
    ]

    try:
        response = await llm.ainvoke(messages)
        return {**state, "final_response": response.content}

    except Exception as e:
        print(f"Synthesize node failed: {e}")
        # Just return raw tool result if synthesis fails
        return {**state, "final_response": state["tool_result"]}


# ── Router ────────────────────────────────────────────────────────────────────
def route_after_classify(state: AgentState) -> Literal["tool_node", "general_node"]:
    if state["category"] in ["search", "calculator", "weather"]:
        return "tool_node"
    return "general_node"


def route_after_tool(state: AgentState) -> Literal["synthesize_node", "general_node"]:
    # If tool returned empty result fall back to general
    if state.get("tool_result"):
        return "synthesize_node"
    return "general_node"


# ── Build Graph ───────────────────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("classify_node", classify_node)
    graph.add_node("tool_node", tool_node)
    graph.add_node("general_node", general_node)
    graph.add_node("synthesize_node", synthesize_node)

    # Entry point
    graph.set_entry_point("classify_node")

    # Edges
    graph.add_conditional_edges(
        "classify_node",
        route_after_classify,
        {
            "tool_node": "tool_node",
            "general_node": "general_node",
        },
    )

    graph.add_conditional_edges(
        "tool_node",
        route_after_tool,
        {
            "synthesize_node": "synthesize_node",
            "general_node": "general_node",
        },
    )

    graph.add_edge("general_node", END)
    graph.add_edge("synthesize_node", END)

    return graph.compile()


# Compiled graph — reused across requests
_graph = build_graph()


# ── Public interface ──────────────────────────────────────────────────────────
async def run_agent(
    user_message: str,
    history: list[BaseMessage],
) -> str:
    """
    Run the LangGraph agent pipeline:
    classify → tool (if needed) → synthesize / general → response
    """
    initial_state: AgentState = {
        "user_message": user_message,
        "history": history,
        "category": "",
        "tool_result": "",
        "final_response": "",
    }

    result = await _graph.ainvoke(initial_state)
    return result["final_response"]