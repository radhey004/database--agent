from contextvars import ContextVar
from typing import Any

from mcp import Client

from .config import MCP_SERVER_URL

from .mcp_auth import (
    create_mcp_context,
)


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

        super().__init__(
            message
        )


# ============================================================
# REQUEST-SCOPED USER CONTEXT
# ============================================================

_current_user_id = ContextVar(
    "mcp_user_id",
    default=None,
)


def set_mcp_user(
    user_id: str,
):

    return _current_user_id.set(
        str(user_id)
    )


def reset_mcp_user(
    token,
):

    _current_user_id.reset(
        token
    )


def get_mcp_user():

    return _current_user_id.get()


# ============================================================
# MCP TOOL CALL
# ============================================================

async def call_tool(
    name: str,
    arguments: dict[str, Any],
):

    user_id = get_mcp_user()

    if not user_id:

        raise MCPToolError(
            tool_name=name,
            message=(
                "MCP user context is missing."
            ),
            retryable=False,
        )

    arguments = dict(
        arguments
    )

    # --------------------------------------------------------
    # The internal authentication context is injected here.
    #
    # The LangGraph agent never sees it.
    # --------------------------------------------------------

    arguments[
        "mcp_context"
    ] = create_mcp_context(
        user_id
    )

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


# ============================================================
# LIST TOOLS
# ============================================================

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