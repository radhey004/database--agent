from typing import Any

from mcp import Client

from .config import MCP_SERVER_URL


class MCPToolError(Exception):

    def __init__(
        self,
        tool_name: str,
        message: str,
        retryable: bool = True,
    ):
        self.tool_name = tool_name
        self.message = message
        self.retryable = retryable

        super().__init__(message)


async def call_tool(
    name: str,
    arguments: dict[str, Any],
):

    try:

        async with Client(
            MCP_SERVER_URL
        ) as client:

            response = await client.call_tool(
                name,
                arguments,
            )

            return response

    except Exception as error:

        raise MCPToolError(
            tool_name=name,
            message=(
                f"MCP tool '{name}' failed: "
                f"{error}"
            ),
            retryable=True,
        ) from error


async def list_tools():

    try:

        async with Client(
            MCP_SERVER_URL
        ) as client:

            return await client.list_tools()

    except Exception as error:

        raise MCPToolError(
            tool_name="list_tools",
            message=str(error),
            retryable=False,
        ) from error