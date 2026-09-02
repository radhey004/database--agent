import os

from dotenv import load_dotenv


load_dotenv()


# ============================================================
# APPLICATION DATABASE
# ============================================================

AUTH_DATABASE_URL = os.getenv(
    "AUTH_DATABASE_URL"
) or os.getenv(
    "DATABASE_URL"
)

# ============================================================
# AUTHENTICATION
# ============================================================

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "change-this-development-secret",
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

JWT_EXPIRE_DAYS = int(
    os.getenv(
        "JWT_EXPIRE_DAYS",
        "7",
    )
)

AUTH_COOKIE_NAME = os.getenv(
    "AUTH_COOKIE_NAME",
    "dbagent_session",
)

AUTH_COOKIE_SECURE = (
    os.getenv(
        "AUTH_COOKIE_SECURE",
        "false",
    ).lower()
    == "true"
)

TERMS_VERSION = os.getenv(
    "TERMS_VERSION",
    "1.0",
)


# ============================================================
# MCP INTERNAL AUTHENTICATION
# ============================================================

MCP_INTERNAL_SECRET = os.getenv(
    "MCP_INTERNAL_SECRET"
)

if not MCP_INTERNAL_SECRET:

    raise RuntimeError(
        "MCP_INTERNAL_SECRET is not configured."
    )


# ============================================================
# GROQ
# ============================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


# ============================================================
# OLLAMA
# ============================================================

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:3b",
)


# ============================================================
# MCP
# ============================================================

MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://127.0.0.1:9000/mcp",
)


# ============================================================
# AGENT
# ============================================================

MAX_SQL_RETRIES = int(
    os.getenv(
        "MAX_SQL_RETRIES",
        "3",
    )
)


# ============================================================
# LANGSMITH
# ============================================================

LANGSMITH_TRACING = os.getenv(
    "LANGSMITH_TRACING",
    "false",
)

LANGSMITH_ENDPOINT = os.getenv(
    "LANGSMITH_ENDPOINT",
    "https://api.smith.langchain.com",
)

LANGSMITH_API_KEY = os.getenv(
    "LANGSMITH_API_KEY"
)

LANGSMITH_PROJECT = os.getenv(
    "LANGSMITH_PROJECT",
    "database-ai-agent-v2",
)