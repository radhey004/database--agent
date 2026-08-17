import json
from typing import Literal, TypedDict

from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from .config import GROQ_API_KEY, OLLAMA_MODEL, OLLAMA_URL
from .mcp_client import call_tool
from .prompts import SQL_PROMPT, ROUTER_PROMPT


# -------------------------
# State
# -------------------------

class State(TypedDict, total=False):
    question: str
    schema: dict
    intent: str
    sql: str
    result: object
    error: str


# -------------------------
# Intent output
# -------------------------

class Intent(BaseModel):
    type: Literal["read", "write", "unrelated"]


# -------------------------
# Models
# -------------------------

groq = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
    temperature=0,
)

ollama = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_URL,
    temperature=0,
)


# -------------------------
# Helpers
# -------------------------

def clean_sql(text: str) -> str:
    return (
        text
        .strip()
        .replace("```sql", "")
        .replace("```", "")
        .strip()
    )


def content_to_text(content):
    """Convert MCP content to normal text."""

    if isinstance(content, str):
        return content

    if hasattr(content, "text"):
        return content.text

    return str(content)


# -------------------------
# Get database schema
# -------------------------

async def get_schema(state: State):

    response = await call_tool(
        "database_schema",
        {}
    )

    schema = json.loads(
        content_to_text(
            response.content[0]
        )
    )

    return {
        "schema": schema
    }


# -------------------------
# Dynamic intent router
# -------------------------

async def classify_intent(state: State):
    """
    Dynamically classify the question as:
    read, write, or unrelated.
    """

    prompt = ROUTER_PROMPT.format(
        schema=state["schema"],
        question=state["question"],
    )

    try:
        # Groq primary.
        router = groq.with_structured_output(Intent)

        result = await router.ainvoke(prompt)

        print("Intent model: Groq")

    except Exception as error:

        print("Groq router failed:", error)
        print("Using Ollama router")

        # Ollama fallback.
        router = ollama.with_structured_output(Intent)

        result = await router.ainvoke(prompt)

    print("Detected intent:", result.type)

    return {
        "intent": result.type
    }


# -------------------------
# Generate SQL
# -------------------------

async def generate_sql(state: State):

    prompt = SQL_PROMPT.format(
        schema=state["schema"],
        question=state["question"],
    )

    try:
        response = await groq.ainvoke(prompt)

        sql = clean_sql(
            response.content
        )

        print("Using Groq")

    except Exception as error:

        print("Groq failed:", error)
        print(
            "Using Ollama backup:",
            OLLAMA_MODEL
        )

        response = await ollama.ainvoke(prompt)

        sql = clean_sql(
            response.content
        )

    print("Generated SQL:", sql)

    return {
        "sql": sql
    }


# -------------------------
# Execute SQL
# -------------------------

async def execute_sql(state: State):

    response = await call_tool(
        "run_sql",
        {
            "query": state["sql"]
        }
    )

    # MCP tool may report an error.
    if response.is_error:
        raise ValueError(
            content_to_text(
                response.content[0]
            )
        )

    result = json.loads(
        content_to_text(
            response.content[0]
        )
    )

    return {
        "result": result
    }


# -------------------------
# Reject request
# -------------------------

async def reject_request(state: State):

    if state["intent"] == "write":
        message = (
            "This database agent is read-only. "
            "INSERT, UPDATE, DELETE and other "
            "write operations are not supported."
        )

    else:
        message = (
            "I can only answer questions related "
            "to the connected PostgreSQL database."
        )

    return {
        "error": message
    }


# -------------------------
# Router
# -------------------------

def route_intent(state: State):

    if state["intent"] == "read":
        return "generate_sql"

    return "reject_request"


# -------------------------
# LangGraph
# -------------------------

graph = StateGraph(State)

graph.add_node(
    "get_schema",
    get_schema
)

graph.add_node(
    "classify_intent",
    classify_intent
)

graph.add_node(
    "generate_sql",
    generate_sql
)

graph.add_node(
    "execute_sql",
    execute_sql
)

graph.add_node(
    "reject_request",
    reject_request
)


graph.add_edge(
    START,
    "get_schema"
)

graph.add_edge(
    "get_schema",
    "classify_intent"
)

graph.add_conditional_edges(
    "classify_intent",
    route_intent,
    {
        "generate_sql": "generate_sql",
        "reject_request": "reject_request",
    }
)

graph.add_edge(
    "generate_sql",
    "execute_sql"
)

graph.add_edge(
    "execute_sql",
    END
)

graph.add_edge(
    "reject_request",
    END
)


agent = graph.compile()


# -------------------------
# Public function
# -------------------------

async def ask_agent(question: str):

    result = await agent.ainvoke({
        "question": question
    })

    if result.get("error"):
        raise ValueError(
            result["error"]
        )

    return {
        "sql": result["sql"],
        "result": result["result"]
    }