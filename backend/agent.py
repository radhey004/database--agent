import json
import uuid
from typing import Literal, TypedDict

from pydantic import BaseModel
from langgraph.graph import (
    StateGraph,
    START,
    END,
)
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from .config import (
    GROQ_API_KEY,
    OLLAMA_MODEL,
    OLLAMA_URL,
)
from .mcp_client import call_tool
from .prompts import (
    SQL_PROMPT,
    ROUTER_PROMPT,
)
from .sql_validator import (
    validate_read_sql,
    validate_write_sql,
)


class State(TypedDict, total=False):

    question: str
    schema: dict
    intent: str
    sql: str
    result: object
    preview: dict
    error: str
    approval_required: bool
    request_id: str


class Intent(BaseModel):

    type: Literal[
        "read",
        "write",
        "unrelated",
    ]


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


pending_requests = {}


BLOCKED_COMMANDS = (
    "GRANT",
    "REVOKE",
    "COMMENT",
    "BEGIN",
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    "RELEASE",
    "CREATE EXTENSION",
    "CREATE DATABASE",
    "DROP DATABASE",
    "ALTER DATABASE",
    "COPY",
)


def clean_sql(text: str) -> str:

    return (
        text
        .strip()
        .replace("```sql", "")
        .replace("```", "")
        .strip()
    )


def content_to_text(content):

    if isinstance(content, str):
        return content

    if hasattr(content, "text"):
        return content.text

    return str(content)


def check_blocked_command(
    question: str
):

    normalized = " ".join(
        question.upper().split()
    )

    for command in BLOCKED_COMMANDS:

        if (
            normalized == command
            or normalized.startswith(
                command + " "
            )
            or normalized.startswith(
                command + ";"
            )
        ):

            raise ValueError(
                "SQL command is not allowed: "
                + command
            )


async def get_schema(state: State):

    response = await call_tool(
        "database_schema",
        {}
    )

    if response.is_error:

        raise ValueError(
            content_to_text(
                response.content[0]
            )
        )

    schema = json.loads(
        content_to_text(
            response.content[0]
        )
    )

    return {
        "schema": schema
    }


async def classify_intent(
    state: State
):

    prompt = ROUTER_PROMPT.format(
        schema=state["schema"],
        question=state["question"],
    )

    try:

        router = groq.with_structured_output(
            Intent
        )

        result = await router.ainvoke(
            prompt
        )

        print(
            "Intent model: Groq"
        )

    except Exception as error:

        print(
            "Groq router failed:",
            error
        )

        router = ollama.with_structured_output(
            Intent
        )

        result = await router.ainvoke(
            prompt
        )

        print(
            "Intent model: Ollama"
        )

    print(
        "Detected intent:",
        result.type
    )

    return {
        "intent": result.type
    }


async def generate_sql(
    state: State
):

    prompt = SQL_PROMPT.format(
        schema=state["schema"],
        question=state["question"],
    )

    try:

        response = await groq.ainvoke(
            prompt
        )

        sql = clean_sql(
            response.content
        )

        print(
            "SQL model: Groq"
        )

    except Exception as error:

        print(
            "Groq SQL generation failed:",
            error
        )

        response = await ollama.ainvoke(
            prompt
        )

        sql = clean_sql(
            response.content
        )

        print(
            "SQL model: Ollama"
        )

    print(
        "Generated SQL:",
        sql
    )

    if not sql:

        raise ValueError(
            "The AI could not generate "
            "a valid SQL query."
        )

    if state["intent"] == "read":

        validate_read_sql(sql)

    elif state["intent"] == "write":

        validate_write_sql(sql)

    else:

        raise ValueError(
            "Invalid intent for SQL generation."
        )

    return {
        "sql": sql
    }


async def execute_read_sql(
    state: State
):

    response = await call_tool(
        "run_sql",
        {
            "query": state["sql"]
        }
    )

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


async def request_approval(
    state: State
):

    # Validate before preview.
    validate_write_sql(
        state["sql"]
    )

    # Generate a preview before asking
    # the human for approval.
    response = await call_tool(
        "preview_modification",
        {
            "query": state["sql"]
        }
    )

    if response.is_error:

        raise ValueError(
            content_to_text(
                response.content[0]
            )
        )

    preview = json.loads(
        content_to_text(
            response.content[0]
        )
    )

    request_id = str(
        uuid.uuid4()
    )

    pending_requests[request_id] = {
        "sql": state["sql"],
        "question": state["question"],
        "intent": state["intent"],
        "preview": preview,
    }

    print(
        "Approval required:",
        request_id
    )

    return {
        "approval_required": True,
        "request_id": request_id,
        "preview": preview,
    }


async def reject_request(
    state: State
):

    return {
        "error": (
            "I can only answer questions "
            "related to the connected "
            "PostgreSQL database."
        )
    }


def route_intent(
    state: State
):

    if state["intent"] == "read":

        return "generate_sql"

    if state["intent"] == "write":

        return "generate_sql"

    return "reject_request"


def route_after_sql(
    state: State
):

    if state["intent"] == "read":

        return "execute_read_sql"

    if state["intent"] == "write":

        return "request_approval"

    return "reject_request"


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
    "execute_read_sql",
    execute_read_sql
)

graph.add_node(
    "request_approval",
    request_approval
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
        "generate_sql":
            "generate_sql",

        "reject_request":
            "reject_request",
    }
)

graph.add_conditional_edges(
    "generate_sql",
    route_after_sql,
    {
        "execute_read_sql":
            "execute_read_sql",

        "request_approval":
            "request_approval",

        "reject_request":
            "reject_request",
    }
)

graph.add_edge(
    "execute_read_sql",
    END
)

graph.add_edge(
    "request_approval",
    END
)

graph.add_edge(
    "reject_request",
    END
)


agent = graph.compile()


async def ask_agent(
    question: str
):

    question = question.strip()

    if not question:

        raise ValueError(
            "Question is required."
        )

    check_blocked_command(
        question
    )

    result = await agent.ainvoke(
        {
            "question": question
        }
    )

    if result.get("error"):

        raise ValueError(
            result["error"]
        )

    if result.get(
        "approval_required"
    ):

        return {
            "status":
                "pending_approval",

            "request_id":
                result["request_id"],

            "question":
                question,

            "sql":
                result["sql"],

            "preview":
                result["preview"],
        }

    return {
        "status":
            "completed",

        "sql":
            result["sql"],

        "result":
            result["result"],
    }


async def approve_request(
    request_id: str
):

    request = pending_requests.get(
        request_id
    )

    if not request:

        raise ValueError(
            "Approval request not found "
            "or expired."
        )

    sql = request["sql"]

    # Validate AGAIN immediately
    # before actual execution.
    validate_write_sql(sql)

    response = await call_tool(
        "run_modification",
        {
            "query": sql
        }
    )

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

    del pending_requests[
        request_id
    ]

    return {
        "status":
            "approved_and_executed",

        "sql":
            sql,

        "preview":
            request["preview"],

        "result":
            result,
    }


def reject_approval(
    request_id: str
):

    request = pending_requests.pop(
        request_id,
        None
    )

    if not request:

        raise ValueError(
            "Approval request not found "
            "or expired."
        )

    return {
        "status":
            "rejected",

        "sql":
            request["sql"],

        "preview":
            request["preview"],

        "message": (
            "The modification was rejected. "
            "No database changes were made."
        ),
    }