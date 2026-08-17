from mcp import Client

from .config import MCP_SERVER_URL


async def call_tool(
    name: str,
    arguments: dict
):
    """
    Call a tool on the separate MCP server.
    """

    async with Client(
        MCP_SERVER_URL
    ) as client:

        return await client.call_tool(
            name,
            arguments
        )