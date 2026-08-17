import json

from mcp.server.mcpserver import MCPServer

from .database import get_schema, execute_query


mcp = MCPServer("Database Server")


@mcp.tool()
def database_schema() -> str:
    """Get the PostgreSQL database schema."""

    print("MCP: database_schema called")

    schema = get_schema()

    print("MCP: schema:", schema)

    # Return plain text instead of a Python dict.
    return json.dumps(schema)


@mcp.tool()
def run_sql(query: str) -> str:
    """Execute a read-only SELECT query."""

    print("MCP: run_sql called:", query)

    result = execute_query(query)

    print("MCP: result:", result)

    # Return plain text instead of a Python list.
    return json.dumps(result, default=str)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=9000,
        stateless_http=True,
        json_response=True,
    )