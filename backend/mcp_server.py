import json

from mcp.server.mcpserver import MCPServer

from .database import (
    get_schema,
    execute_query,
    preview_modification as preview_modification_db,
    execute_modification,
)


mcp = MCPServer(
    "Database Server"
)


@mcp.tool()
def database_schema() -> str:
    """Get the PostgreSQL database schema."""

    print(
        "MCP: database_schema called"
    )

    schema = get_schema()

    print(
        "MCP: schema:",
        schema
    )

    return json.dumps(schema)


@mcp.tool()
def run_sql(query: str) -> str:
    """Execute a read-only SELECT query."""

    print(
        "MCP: run_sql called:",
        query
    )

    result = execute_query(
        query
    )

    print(
        "MCP: result:",
        result
    )

    return json.dumps(
        result,
        default=str
    )


@mcp.tool()
def preview_modification(
    query: str
) -> str:
    """
    Preview a database modification without
    committing the modification.
    """

    print(
        "MCP: preview_modification called:",
        query
    )

    result = preview_modification_db(
        query
    )

    print(
        "MCP: preview:",
        result
    )

    return json.dumps(
        result,
        default=str
    )


@mcp.tool()
def run_modification(
    query: str
) -> str:
    """
    Execute a modification after human approval.
    """

    print(
        "MCP: run_modification called:",
        query
    )

    result = execute_modification(
        query
    )

    print(
        "MCP: modification result:",
        result
    )

    return json.dumps(
        result,
        default=str
    )


if __name__ == "__main__":

    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=9000,
        stateless_http=True,
        json_response=True,
    )