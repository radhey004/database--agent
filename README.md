# Database AI Agent

A minimal natural-language PostgreSQL database agent that converts user questions into safe, read-only SQL and executes them through a separate MCP server.

## Features

- Natural-language database queries
- Dynamic **LangGraph intent routing**
  - `read` → generate and execute SQL
  - `write` → reject
  - `unrelated` → reject
- Groq as the primary LLM
- Ollama `qwen2.5:3b` as the local fallback
- Separate MCP client-server architecture
- MCP communication over **Streamable HTTP**
- Dynamic PostgreSQL schema discovery
- SQLGlot AST validation
- Only one `SELECT` statement is allowed
- Maximum 100 returned rows
- Neon PostgreSQL support
- React frontend + FastAPI backend

---

## Architecture

```mermaid
flowchart TB
    U[User] --> R[React Frontend]

    R -->|POST /ask| API[FastAPI Backend]

    API --> LG[LangGraph Agent]

    LG --> ROUTER[Dynamic Intent Router]

    ROUTER -->|read| SQL[SQL Generation]
    ROUTER -->|write| RW[Reject Write Request]
    ROUTER -->|unrelated| OFF[Reject Unrelated Question]

    SQL --> VAL[SQLGlot AST Validation]

    VAL -->|Valid SELECT| MC[MCP Client]

    MC -->|Streamable HTTP| MS[MCP Server :9000/mcp]

    MS --> TOOL1[database_schema]
    MS --> TOOL2[run_sql]

    TOOL1 --> DB[Neon PostgreSQL]
    TOOL2 --> DB

    DB --> TOOL2
    TOOL2 --> MS
    MS --> MC
    MC --> API
    API --> R

    GROQ[Groq<br/>openai/gpt-oss-120b] --> LG
    OLLAMA[Ollama<br/>qwen2.5:3b] -. fallback .-> LG
```

---

## LangGraph Flow

The agent uses LangGraph to make the routing decision before SQL generation.

```mermaid
flowchart TD
    START([START])
    SCHEMA[get_schema]
    INTENT[classify_intent]

    READ{Intent}

    SQL[generate_sql]
    VALIDATE[SQLGlot validation]
    EXEC[execute_sql]
    END([END])

    REJECT[reject_request]

    START --> SCHEMA
    SCHEMA --> INTENT
    INTENT --> READ

    READ -->|read| SQL
    READ -->|write| REJECT
    READ -->|unrelated| REJECT

    SQL --> VALIDATE
    VALIDATE --> EXEC
    EXEC --> END

    REJECT --> END
```

### Intent routing

```mermaid
flowchart LR
    Q[User Question] --> I[LLM Intent Router]

    I --> R[READ]
    I --> W[WRITE]
    I --> U[UNRELATED]

    R --> S[Generate SELECT SQL]
    W --> X[Reject]
    U --> Y[Reject]
```

The router is LLM-based rather than a hardcoded keyword list. This allows natural requests such as:

- `How many users are there?` → `read`
- `Give me the customer who spends the most money.` → `read`
- `Put Rahul into the users table.` → `write`
- `Insert a new product.` → `write`
- `Who is the president of India?` → `unrelated`

---

## SQL Safety Flow

The LLM is **not trusted to enforce database safety by itself**.

Every generated query passes through SQLGlot before it reaches PostgreSQL.

```mermaid
flowchart LR
    LLM[LLM Generated SQL]
    PARSE[SQLGlot PostgreSQL Parser]
    ONE{Exactly one statement?}
    SELECT{Root AST is SELECT?}
    MCP[MCP run_sql]
    DB[Neon PostgreSQL]
    REJECT[Reject Query]

    LLM --> PARSE
    PARSE --> ONE

    ONE -->|No| REJECT
    ONE -->|Yes| SELECT

    SELECT -->|No| REJECT
    SELECT -->|Yes| MCP

    MCP --> DB
```

The database layer also limits the returned result set to **100 rows**.

---

## LLM Strategy

```mermaid
flowchart TD
    Q[LLM Request] --> G[Groq<br/>openai/gpt-oss-120b]

    G -->|Success| OUT[Continue]
    G -->|Failure| O[Ollama<br/>qwen2.5:3b]

    O --> OUT
```

Groq is used as the primary model. If the Groq request fails, the agent falls back to the local Ollama model.

---

## MCP Architecture

The project intentionally separates the AI agent from the database tools.

```mermaid
sequenceDiagram
    participant User
    participant React
    participant FastAPI
    participant LangGraph
    participant MCPClient as MCP Client
    participant MCPServer as MCP Server
    participant Neon as Neon PostgreSQL

    User->>React: Natural-language question
    React->>FastAPI: POST /ask
    FastAPI->>LangGraph: ask_agent(question)

    LangGraph->>MCPClient: database_schema()
    MCPClient->>MCPServer: Streamable HTTP
    MCPServer->>Neon: Read schema
    Neon-->>MCPServer: Schema
    MCPServer-->>MCPClient: Schema
    MCPClient-->>LangGraph: Schema

    LangGraph->>LangGraph: Classify intent
    LangGraph->>LangGraph: Generate SELECT SQL
    LangGraph->>LangGraph: SQLGlot validation

    LangGraph->>MCPClient: run_sql(query)
    MCPClient->>MCPServer: Streamable HTTP
    MCPServer->>Neon: Execute SELECT
    Neon-->>MCPServer: Rows
    MCPServer-->>MCPClient: JSON result
    MCPClient-->>LangGraph: Result

    LangGraph-->>FastAPI: SQL + result
    FastAPI-->>React: JSON response
    React-->>User: SQL + database result
```

---

## Project Structure

```text
dbagent_mcp/
│
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI API
│   ├── agent.py             # LangGraph agent + intent router
│   ├── prompts.py           # Router and SQL prompts
│   ├── mcp_client.py        # MCP client
│   ├── mcp_server.py        # MCP server and database tools
│   ├── database.py          # PostgreSQL access + row limit
│   ├── sql_validator.py     # SQLGlot AST validation
│   └── config.py            # Environment variables
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # React UI
│   │   ├── api.js           # Backend API call
│   │   └── main.jsx
│   ├── package.json
│   └── index.html
│
├── tests/
│   └── test_agent.py        # SQL safety tests
│
├── test_mcp.py              # MCP tool test
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## MCP Tools

The MCP server exposes two tools:

### `database_schema()`

Reads the PostgreSQL schema from `information_schema.columns`.

It allows the agent to work with the connected database schema dynamically instead of hardcoding table definitions.

Example:

```json
{
  "users": ["id", "name", "email", "city"],
  "products": ["id", "name", "price", "stock"]
}
```

### `run_sql(query)`

Executes a validated read-only SQL query.

The database layer:

1. Parses the SQL using SQLGlot.
2. Requires exactly one statement.
3. Requires the root AST node to be `SELECT`.
4. Executes the query.
5. Returns at most 100 rows.

---

## Database

The project works with **Neon PostgreSQL** using the PostgreSQL connection string stored in `.env`.

Example:

```env
DATABASE_URL=postgresql://USER:PASSWORD@YOUR-ENDPOINT.neon.tech/neondb?sslmode=require
GROQ_API_KEY=your_groq_api_key
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
MCP_SERVER_URL=http://127.0.0.1:9000/mcp
```

Never commit `.env`.

Use `.env.example` as the template.

---

## Setup

### 1. Create Python environment

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Create `.env`:

```bash
cp .env.example .env
```

Then add:

```env
DATABASE_URL=your_neon_postgresql_connection_string
GROQ_API_KEY=your_groq_api_key
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
MCP_SERVER_URL=http://127.0.0.1:9000/mcp
```

### 3. Start Ollama

Make sure Ollama is running:

```bash
ollama serve
```

In another terminal:

```bash
ollama pull qwen2.5:3b
```

### 4. Start MCP Server

From the project root:

```bash
source .venv/bin/activate
python -m backend.mcp_server
```

MCP endpoint:

```text
http://127.0.0.1:9000/mcp
```

### 5. Start FastAPI

Open another terminal:

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8001
```

Backend:

```text
http://127.0.0.1:8001
```

Health check:

```bash
curl http://localhost:8001/health
```

Expected:

```json
{"status":"ok"}
```

### 6. Start React

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

---

## Example Questions

The agent can answer database questions such as:

```text
How many users are there?

Which products have less than 10 items in stock?

Which product has been ordered the most?

Give me the customer who spends the most money.

Show the latest orders.

Which city has the most customers?
```

For example:

```text
Give me the customer who spends the most money.
```

can result in a multi-table aggregation using:

- `users`
- `orders`
- `order_items`

and calculate total spending using:

```sql
SUM(quantity * price)
```

---

## Safety Tests

The project was tested against:

### Read query

```text
How many users are there?
```

Expected:

```text
READ → Generate SQL → Validate → MCP → Neon
```

### Write query

```text
Insert a new user named Test User.
```

Expected:

```text
WRITE → Reject
```

### Natural-language write request

```text
Put Rahul into the users table.
```

Expected:

```text
WRITE → Reject
```

### Unrelated question

```text
Who is the president of India?
```

Expected:

```text
UNRELATED → Reject
```

### Complex read query

```text
Give me the customer who spends the most money.
```

Expected:

```text
READ → Generate JOIN/aggregation SQL → Validate → Execute
```

---

## Testing

Run:

```bash
pytest
```

Test the MCP server separately:

```bash
python test_mcp.py
```

The MCP test verifies that the client can connect to the separate MCP server and call tools such as:

```text
database_schema
run_sql
```

---

## Security Model

The current project is intentionally **read-only**.

```mermaid
flowchart TD
    Q[User Question]
    I[Intent Router]
    SQL[Generated SQL]
    AST[SQLGlot AST]
    MCP[MCP Server]
    DB[Neon PostgreSQL]

    Q --> I
    I -->|write| X1[Rejected]
    I -->|unrelated| X2[Rejected]
    I -->|read| SQL
    SQL --> AST

    AST -->|INSERT / UPDATE / DELETE / DROP / ALTER| X3[Rejected]
    AST -->|Valid SELECT| MCP
    MCP --> DB
```

The important security principle is **defense in depth**:

- Intent router blocks write intent.
- SQL prompt asks for `SELECT` only.
- SQLGlot validates the generated SQL structurally.
- MCP exposes controlled database tools.
- Result size is limited to 100 rows.

For production deployment, use a dedicated PostgreSQL role with only the required read permissions, MCP authentication, HTTPS, query timeouts, and stronger database-level access controls.

---

## Limitations

- The agent currently works with PostgreSQL.
- It is read-only by design.
- It returns database results rather than generating a long natural-language explanation of every result.
- LLM-generated SQL can still be semantically incorrect even when it is syntactically valid.
- Complex schemas may require better schema descriptions or additional metadata.
- The current MCP server is intended for a trusted environment and should use authentication before public deployment.
- The Ollama fallback requires the local `qwen2.5:3b` model to be installed.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Backend API | FastAPI |
| Agent orchestration | LangGraph |
| Primary LLM | Groq `openai/gpt-oss-120b` |
| Backup LLM | Ollama `qwen2.5:3b` |
| Tool protocol | MCP |
| MCP transport | Streamable HTTP |
| Database | Neon PostgreSQL |
| SQL validation | SQLGlot |
| Database driver | psycopg2 |
| Testing | pytest |

---

## Why MCP?

Instead of allowing the LangGraph agent to directly access PostgreSQL, database operations are exposed as MCP tools.

```mermaid
flowchart LR
    A[LangGraph Agent] --> B[MCP Client]
    B -->|Streamable HTTP| C[MCP Server]
    C --> D[Database Tools]
    D --> E[Neon PostgreSQL]
```

This separation makes the database tools independently exposed and easier to control, test, and replace.

---

## Project Goal

The goal of this project is to demonstrate how an LLM-powered agent can safely interact with a real PostgreSQL database through:

**Natural Language → Intent Routing → SQL Generation → AST Validation → MCP Tool → PostgreSQL**

while keeping database access read-only and separated from the main agent process.
