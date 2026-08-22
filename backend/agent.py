import json
import uuid

from typing import (
    Literal,
    TypedDict,
)

from pydantic import BaseModel

from langchain_groq import (
    ChatGroq,
)

from langchain_ollama import (
    ChatOllama,
)

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from .config import (
    GROQ_API_KEY,
    OLLAMA_MODEL,
    OLLAMA_URL,
    MAX_SQL_RETRIES,
)

from .mcp_client import (
    call_tool,
)

from .prompts import (
    SQL_PROMPT,
    ROUTER_PROMPT,
)

from .sql_validator import (
    validate_read_sql,
    validate_write_sql,
    validate_schema_usage,
)

from .query_validator import (
    validate_query_intent,
)


class State(
    TypedDict,
    total=False,
):

    question: str

    connection_id: str

    schema: dict

    intent: str

    sql: str

    result: object

    preview: dict

    error: str

    sql_error: str

    semantic_error: str

    retry_count: int

    approval_required: bool

    request_id: str


class Intent(
    BaseModel
):

    intent: Literal[
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


# ============================================================
# HELPERS
# ============================================================

def clean_sql(
    text: str,
):

    text = text.strip()

    if "```sql" in text:

        text = text.split(
            "```sql",
            1,
        )[1]

    if "```" in text:

        text = text.split(
            "```",
            1,
        )[0]

    return text.strip()


def content_to_text(
    content,
):

    if isinstance(
        content,
        str,
    ):

        return content

    if hasattr(
        content,
        "text",
    ):

        return content.text

    return str(
        content
    )


def normalize_question(
    question: str,
):

    return (
        question.lower()
        .strip()
        .replace(
            "?",
            "",
        )
    )


# ============================================================
# GET DATABASE SCHEMA
# ============================================================

async def get_schema(
    state: State,
):

    response = await call_tool(
        "database_schema",
        {
            "connection_id":
                state["connection_id"],
        },
    )

    content = content_to_text(
        response.content[0]
    )

    data = json.loads(
        content
    )

    if not data.get(
        "success"
    ):

        raise ValueError(
            data.get(
                "error",
                "Schema discovery failed.",
            )
        )

    return {
        "schema":
            data["schema"]
    }


# ============================================================
# FIND TABLE NAME IN QUESTION
# ============================================================

def find_table_in_question(
    question: str,
    schema: dict,
):

    normalized = normalize_question(
        question
    )

    for table_name in schema.keys():

        table_lower = (
            table_name.lower()
        )

        if table_lower in normalized:

            return table_name

    return None


# ============================================================
# DETECT SCHEMA QUESTION
# ============================================================

def get_schema_question_type(
    question: str,
    schema: dict,
):

    normalized = normalize_question(
        question
    )

    table_name = (
        find_table_in_question(
            question,
            schema,
        )
    )

    # --------------------------------------------------------
    # TABLE COUNT
    # --------------------------------------------------------

    if (
        (
            "how many tables"
            in normalized
        )
        or (
            "number of tables"
            in normalized
        )
        or (
            "count tables"
            in normalized
        )
    ):

        return (
            "table_count",
            None,
        )

    # --------------------------------------------------------
    # TABLE NAMES
    # --------------------------------------------------------

    table_name_patterns = (
        "give name of each table",
        "give names of tables",
        "give name of all tables",
        "give names of all tables",
        "list tables",
        "list all tables",
        "show tables",
        "show all tables",
        "what are the tables",
        "which tables",
        "name of tables",
        "names of tables",
        "name of the tables",
        "names of the tables",
        "what is the name of tables",
        "what are the names of tables",
    )

    if any(
        pattern in normalized
        for pattern in (
            table_name_patterns
        )
    ):

        return (
            "table_names",
            None,
        )

    # --------------------------------------------------------
    # FULL DATABASE SCHEMA
    # --------------------------------------------------------

    schema_patterns = (
        "show database schema",
        "show the database schema",
        "show schema",
        "show the schema",
        "database schema",
        "full schema",
        "complete schema",
        "describe database",
        "describe the database",
    )

    if any(
        pattern in normalized
        for pattern in (
            schema_patterns
        )
    ):

        return (
            "full_schema",
            None,
        )

    # --------------------------------------------------------
    # TABLE COLUMNS
    # --------------------------------------------------------

    column_words = (
        "column",
        "columns",
        "fields",
        "field",
    )

    if (
        table_name
        and any(
            word in normalized
            for word in (
                column_words
            )
        )
    ):

        return (
            "table_columns",
            table_name,
        )

    # --------------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------------

    primary_key_patterns = (
        "primary key",
        "primary keys",
    )

    if (
        table_name
        and any(
            pattern in normalized
            for pattern in (
                primary_key_patterns
            )
        )
    ):

        return (
            "primary_key",
            table_name,
        )

    return (
        None,
        None,
    )


# ============================================================
# EXTRACT PRIMARY KEY
# ============================================================

def get_primary_key_columns(
    table_data: dict,
):

    primary_keys = []

    for column in table_data.get(
        "columns",
        [],
    ):

        if column.get(
            "primary_key",
            False,
        ):

            primary_keys.append(
                column.get(
                    "name"
                )
            )

    return primary_keys


# ============================================================
# ANSWER SCHEMA QUESTION
# ============================================================

async def answer_schema_question(
    state: State,
):

    schema = state.get(
        "schema",
        {},
    )

    question_type, table_name = (
        get_schema_question_type(
            state["question"],
            schema,
        )
    )

    table_names = sorted(
        schema.keys()
    )

    # --------------------------------------------------------
    # TABLE COUNT
    # --------------------------------------------------------

    if (
        question_type ==
        "table_count"
    ):

        return {
            "sql": "",

            "result": {
                "success": True,

                "row_count": 1,

                "rows": [
                    {
                        "table_count":
                            len(
                                table_names
                            )
                    }
                ],
            },
        }

    # --------------------------------------------------------
    # TABLE NAMES
    # --------------------------------------------------------

    if (
        question_type ==
        "table_names"
    ):

        return {
            "sql": "",

            "result": {
                "success": True,

                "row_count":
                    len(
                        table_names
                    ),

                "rows": [
                    {
                        "table_name":
                            table_name
                    }
                    for table_name
                    in table_names
                ],
            },
        }

    # --------------------------------------------------------
    # FULL DATABASE SCHEMA
    # --------------------------------------------------------

    if (
        question_type ==
        "full_schema"
    ):

        rows = []

        for table_name in table_names:

            table_data = (
                schema[
                    table_name
                ]
            )

            columns = (
                table_data.get(
                    "columns",
                    [],
                )
            )

            for column in columns:

                rows.append(
                    {
                        "table_name":
                            table_name,

                        "column_name":
                            column.get(
                                "name",
                                "",
                            ),

                        "data_type":
                            column.get(
                                "type",
                                column.get(
                                    "data_type",
                                    "",
                                ),
                            ),

                        "primary_key":
                            column.get(
                                "primary_key",
                                False,
                            ),

                        "nullable":
                            column.get(
                                "nullable",
                                True,
                            ),
                    }
                )

        return {
            "sql": "",

            "result": {
                "success": True,

                "row_count":
                    len(
                        rows
                    ),

                "rows":
                    rows,
            },
        }

    # --------------------------------------------------------
    # TABLE COLUMNS
    # --------------------------------------------------------

    if (
        question_type ==
        "table_columns"
        and table_name
    ):

        table_data = (
            schema.get(
                table_name,
                {},
            )
        )

        columns = (
            table_data.get(
                "columns",
                [],
            )
        )

        rows = []

        for column in columns:

            rows.append(
                {
                    "column_name":
                        column.get(
                            "name",
                            "",
                        ),

                    "data_type":
                        column.get(
                            "type",
                            column.get(
                                "data_type",
                                "",
                            ),
                        ),

                    "primary_key":
                        column.get(
                            "primary_key",
                            False,
                        ),

                    "nullable":
                        column.get(
                            "nullable",
                            True,
                        ),
                }
            )

        return {
            "sql": "",

            "result": {
                "success": True,

                "table":
                    table_name,

                "row_count":
                    len(
                        rows
                    ),

                "rows":
                    rows,
            },
        }

    # --------------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------------

    if (
        question_type ==
        "primary_key"
        and table_name
    ):

        table_data = (
            schema.get(
                table_name,
                {},
            )
        )

        primary_keys = (
            get_primary_key_columns(
                table_data
            )
        )

        rows = [
            {
                "table_name":
                    table_name,

                "primary_key":
                    key,
            }
            for key in primary_keys
        ]

        return {
            "sql": "",

            "result": {
                "success": True,

                "table":
                    table_name,

                "row_count":
                    len(
                        rows
                    ),

                "rows":
                    rows,
            },
        }

    return {
        "error":
            "Unable to answer "
            "the schema question.",
    }


# ============================================================
# ROUTE AFTER SCHEMA
# ============================================================

def route_after_schema(
    state: State,
):

    question_type, _ = (
        get_schema_question_type(
            state["question"],
            state.get(
                "schema",
                {},
            ),
        )
    )

    if question_type:

        return (
            "answer_schema_question"
        )

    return (
        "classify_intent"
    )


# ============================================================
# CLASSIFY INTENT
# ============================================================

async def classify_intent(
    state: State,
):

    prompt = ROUTER_PROMPT.format(
        schema=state["schema"],
        question=state["question"],
    )

    try:

        response = await groq.ainvoke(
            prompt
        )

        raw = (
            response.content
            .strip()
            .lower()
        )

        if raw in (
            "read",
            "write",
            "unrelated",
        ):

            intent = raw

        else:

            raise ValueError(
                f"Unexpected router output: "
                f"{raw}"
            )

        print(
            "Intent model: Groq"
        )

    except Exception as error:

        print(
            "Groq router failed:",
            error,
        )

        response = await ollama.ainvoke(
            prompt
        )

        raw = (
            response.content
            .strip()
            .lower()
        )

        if raw == "read":

            intent = "read"

        elif raw == "write":

            intent = "write"

        else:

            intent = "unrelated"

        print(
            "Intent model: Ollama"
        )

    return {
        "intent": intent
    }


# ============================================================
# GENERATE SQL
# ============================================================

async def generate_sql(
    state: State,
):

    prompt = SQL_PROMPT.format(
        schema=state["schema"],
        question=state["question"],
        sql_error=state.get(
            "sql_error",
            "",
        ),
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
            error,
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

    try:

        validate_schema_usage(
            sql,
            state["schema"],
        )

        if state["intent"] == "read":

            validate_read_sql(
                sql
            )

        elif state["intent"] == "write":

            validate_write_sql(
                sql
            )

        print(
            "Generated SQL:",
            sql,
        )

    except Exception as error:

        retry_count = (
            state.get(
                "retry_count",
                0,
            )
            + 1
        )

        print(
            "SQL validation failed:",
            error,
        )

        if (
            retry_count >=
            MAX_SQL_RETRIES
        ):

            raise ValueError(
                f"SQL generation failed after "
                f"{MAX_SQL_RETRIES} attempts: "
                f"{error}"
            )

        return {
            "sql": sql,

            "sql_error":
                str(
                    error
                ),

            "retry_count":
                retry_count,
        }

    return {
        "sql": sql,

        "sql_error": "",
    }


# ============================================================
# ROUTE AFTER SQL GENERATION
# ============================================================

def route_after_generation(
    state: State,
):

    if state.get(
        "sql_error"
    ):

        return (
            "generate_sql"
        )

    if state["intent"] == "read":

        return (
            "execute_read_sql"
        )

    if state["intent"] == "write":

        return (
            "request_approval"
        )

    return (
        "reject_request"
    )


# ============================================================
# EXECUTE READ SQL
# ============================================================

async def execute_read_sql(
    state: State,
):

    response = await call_tool(
        "run_sql",
        {
            "connection_id":
                state["connection_id"],

            "query":
                state["sql"],
        },
    )

    content = content_to_text(
        response.content[0]
    )

    data = json.loads(
        content
    )

    if not data.get(
        "success"
    ):

        retry_count = (
            state.get(
                "retry_count",
                0,
            )
            + 1
        )

        if (
            retry_count >=
            MAX_SQL_RETRIES
        ):

            raise ValueError(
                data.get(
                    "error",
                    "SQL execution failed.",
                )
            )

        return {
            "sql_error":
                data.get(
                    "error",
                    "SQL execution failed.",
                ),

            "retry_count":
                retry_count,
        }

    return {
        "result": data,

        "sql_error": "",
    }


# ============================================================
# ROUTE AFTER EXECUTION
# ============================================================

def route_after_execution(
    state: State,
):

    if state.get(
        "sql_error"
    ):

        return (
            "generate_sql"
        )

    return (
        "finish_read"
    )


# ============================================================
# REQUEST APPROVAL
# ============================================================

async def request_approval(
    state: State,
):

    validate_write_sql(
        state["sql"]
    )

    response = await call_tool(
        "preview_modification",
        {
            "connection_id":
                state["connection_id"],

            "query":
                state["sql"],
        },
    )

    data = json.loads(
        content_to_text(
            response.content[0]
        )
    )

    if not data.get(
        "success"
    ):

        raise ValueError(
            data.get(
                "error",
                "Preview failed.",
            )
        )

    request_id = str(
        uuid.uuid4()
    )

    pending_requests[
        request_id
    ] = {
        "connection_id":
            state["connection_id"],

        "sql":
            state["sql"],

        "question":
            state["question"],

        "intent":
            state["intent"],

        "preview":
            data["preview"],
    }

    return {
        "approval_required": True,

        "request_id":
            request_id,

        "preview":
            data["preview"],
    }


# ============================================================
# REJECT UNRELATED REQUEST
# ============================================================

async def reject_request(
    state: State,
):

    return {
        "error": (
            "This request is not related "
            "to the connected database."
        )
    }


# ============================================================
# ROUTE INTENT
# ============================================================

def route_intent(
    state: State,
):

    if state["intent"] in (
        "read",
        "write",
    ):

        return (
            "generate_sql"
        )

    return (
        "reject_request"
    )


# ============================================================
# LANGGRAPH
# ============================================================

graph = StateGraph(
    State
)


graph.add_node(
    "get_schema",
    get_schema,
)


graph.add_node(
    "answer_schema_question",
    answer_schema_question,
)


graph.add_node(
    "classify_intent",
    classify_intent,
)


graph.add_node(
    "generate_sql",
    generate_sql,
)


graph.add_node(
    "execute_read_sql",
    execute_read_sql,
)


graph.add_node(
    "request_approval",
    request_approval,
)


graph.add_node(
    "reject_request",
    reject_request,
)


graph.add_edge(
    START,
    "get_schema",
)


graph.add_conditional_edges(
    "get_schema",
    route_after_schema,
    {
        "answer_schema_question":
            "answer_schema_question",

        "classify_intent":
            "classify_intent",
    },
)


graph.add_edge(
    "answer_schema_question",
    END,
)


graph.add_conditional_edges(
    "classify_intent",
    route_intent,
    {
        "generate_sql":
            "generate_sql",

        "reject_request":
            "reject_request",
    },
)


graph.add_conditional_edges(
    "generate_sql",
    route_after_generation,
    {
        "generate_sql":
            "generate_sql",

        "execute_read_sql":
            "execute_read_sql",

        "request_approval":
            "request_approval",

        "reject_request":
            "reject_request",
    },
)


graph.add_conditional_edges(
    "execute_read_sql",
    route_after_execution,
    {
        "generate_sql":
            "generate_sql",

        "finish_read":
            END,
    },
)


graph.add_edge(
    "request_approval",
    END,
)


graph.add_edge(
    "reject_request",
    END,
)


agent = graph.compile()


# ============================================================
# ASK AGENT
# ============================================================

async def ask_agent(
    question: str,
    connection_id: str,
):

    question = question.strip()

    connection_id = (
        connection_id.strip()
    )

    if not question:

        raise ValueError(
            "Question is required."
        )

    if not connection_id:

        raise ValueError(
            "Database connection ID "
            "is required."
        )

    result = await agent.ainvoke(
        {
            "question": question,

            "connection_id":
                connection_id,

            "retry_count": 0,
        }
    )

    if result.get(
        "error"
    ):

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
            result.get(
                "sql",
                "",
            ),

        "result":
            result.get(
                "result",
                {
                    "success": True,
                    "row_count": 0,
                    "rows": [],
                },
            ),
    }


# ============================================================
# APPROVE REQUEST
# ============================================================

async def approve_request(
    request_id: str,
):

    request = pending_requests.get(
        request_id
    )

    if not request:

        raise ValueError(
            "Approval request not found "
            "or expired."
        )

    response = await call_tool(
        "run_modification",
        {
            "connection_id":
                request["connection_id"],

            "query":
                request["sql"],
        },
    )

    data = json.loads(
        content_to_text(
            response.content[0]
        )
    )

    if not data.get(
        "success"
    ):

        raise ValueError(
            data.get(
                "error",
                "Modification failed.",
            )
        )

    del pending_requests[
        request_id
    ]

    return {
        "status":
            "approved_and_executed",

        "sql":
            request["sql"],

        "preview":
            request["preview"],

        "result":
            data.get(
                "result",
                data,
            ),
    }


# ============================================================
# REJECT APPROVAL
# ============================================================

def reject_approval(
    request_id: str,
):

    request = pending_requests.pop(
        request_id,
        None,
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

        "message":
            "No database changes were made.",
    }