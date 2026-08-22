import os

from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
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
# AGENT CONFIGURATION
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