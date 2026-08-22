import json

from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from .config import (
    GROQ_API_KEY,
    OLLAMA_MODEL,
    OLLAMA_URL,
)


# ============================================================
# MODELS
# ============================================================

groq_validator_model = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
    temperature=0,
)

ollama_validator_model = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_URL,
    temperature=0,
)


# ============================================================
# JSON EXTRACTION
# ============================================================

def _extract_json(
    text: str,
) -> dict:

    text = text.strip()

    if "```json" in text:

        text = text.split(
            "```json",
            1,
        )[1]

    if "```" in text:

        text = text.split(
            "```",
            1,
        )[0]

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:

        raise ValueError(
            "Validator returned invalid JSON."
        )

    try:

        return json.loads(
            text[start:end + 1]
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            "Validator returned invalid JSON."
        ) from error


# ============================================================
# INVOKE VALIDATOR
# GROQ PRIMARY
# OLLAMA FALLBACK ONLY
# ============================================================

async def _invoke_validator(
    prompt: str,
    run_name: str,
) -> dict:

    try:

        response = await groq_validator_model.ainvoke(
            prompt,
            config={
                "run_name": run_name,
                "tags": [
                    "validator",
                    "groq",
                ],
            },
        )

        print(
            f"{run_name}: Groq"
        )

    except Exception as error:

        print(
            f"Groq validator failed: {error}"
        )

        response = await ollama_validator_model.ainvoke(
            prompt,
            config={
                "run_name": (
                    f"{run_name}_fallback"
                ),
                "tags": [
                    "validator",
                    "ollama",
                    "fallback",
                ],
            },
        )

        print(
            f"{run_name}: Ollama fallback"
        )

    return _extract_json(
        response.content
    )


# ============================================================
# VALIDATE USER REQUEST
# ============================================================

async def validate_user_request(
    question: str,
    schema: dict,
) -> dict:

    schema_text = json.dumps(
        schema,
        indent=2,
    )

    prompt = f"""
You are a database request validation agent.

Your job is to determine whether a user's
database request can be fulfilled using the
provided database schema.

You are NOT generating SQL.

You are NOT executing SQL.

DATABASE SCHEMA:
{schema_text}

USER REQUEST:
{question}

Rules:

1. Analyze the user's actual database request.

2. Check whether every database field,
table, and operation required by the request
can be supported by the provided schema.

3. If the user requests a field that does not
exist in the schema, the request is INVALID.

4. If the user requests sorting by a field,
that field must exist in the schema.

5. If the user requests filtering by a field,
that field must exist in the schema.

6. If the user requests aggregation using a
field, that field must exist in the schema.

7. For INSERT operations, check whether the
user has provided values for all required
NOT NULL columns that do not have defaults.

8. If a required field is missing from the
user's request, the request is INVALID.

9. Do not invent missing values.

10. Do not assume that a missing field exists.

11. Normal English words such as:
"their", "the", "nonexistent", "all",
"users", "records", "data"
are NOT automatically database columns.

12. A request is VALID only when the database
schema can reasonably support it.

Examples:

Schema:
users(
    id,
    name,
    email NOT NULL,
    city
)

Request:
"Show users ordered by name"

Result:

{{
    "valid": true,
    "reason": "The request can be answered using the schema."
}}

Request:
"Show users ordered by salary"

Result:

{{
    "valid": false,
    "reason": "salary does not exist in the users schema."
}}

Request:
"Add a user named Radhey"

Result:

{{
    "valid": false,
    "reason": "email is required to create a user but was not provided."
}}

Request:
"Add a user named Radhey with email radhey@example.com"

Result:

{{
    "valid": true,
    "reason": "The request provides the required fields."
}}

Return ONLY JSON.

VALID:

{{
    "valid": true,
    "reason": "The request can be answered using the schema."
}}

INVALID:

{{
    "valid": false,
    "reason": "Explain exactly which required table, field, or value is missing."
}}
"""

    result = await _invoke_validator(
        prompt=prompt,
        run_name="request_validation",
    )

    if "valid" not in result:

        raise ValueError(
            "User request validator did not "
            "return a valid result."
        )

    return {
        "valid": bool(
            result["valid"]
        ),
        "reason": str(
            result.get(
                "reason",
                "",
            )
        ),
    }


# ============================================================
# VALIDATE QUERY INTENT
# ============================================================

async def validate_query_intent(
    question: str,
    sql: str,
    schema: dict,
) -> dict:

    schema_text = json.dumps(
        schema,
        indent=2,
    )

    prompt = f"""
You are a semantic SQL validation agent.

Your job is to determine whether the generated
SQL actually satisfies the user's request.

You are NOT executing SQL.

DATABASE SCHEMA:
{schema_text}

USER REQUEST:
{question}

GENERATED SQL:
{sql}

Rules:

1. The SQL must satisfy the user's actual request.

2. Do not accept SQL that silently removes
an important requirement.

3. If the user asks for sorting by a column,
the SQL must implement that sorting.

4. If the user asks for filtering by a condition,
the SQL must implement that filtering.

5. If the user asks for aggregation,
the SQL must perform that aggregation.

6. If the user asks for a specific field,
that field must be represented appropriately.

7. For INSERT operations, the SQL must include
all required NOT NULL columns that have no
database default.

8. Do not accept an INSERT that would fail
because required values are missing.

9. Do not accept SELECT * as a replacement
for a requested operation.

10. Do not accept ORDER BY NULL as a replacement
for requested sorting.

11. Do not accept NULL AS <column> as a
replacement for a missing field.

12. Be strict.

Return ONLY JSON.

VALID:

{{
    "valid": true,
    "reason": "The SQL satisfies the user's request."
}}

INVALID:

{{
    "valid": false,
    "reason": "Explain exactly what requirement is missing."
}}
"""

    result = await _invoke_validator(
        prompt=prompt,
        run_name="semantic_validation",
    )

    if "valid" not in result:

        raise ValueError(
            "Semantic SQL validator did not "
            "return a valid result."
        )

    return {
        "valid": bool(
            result["valid"]
        ),
        "reason": str(
            result.get(
                "reason",
                "",
            )
        ),
    }