import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from pydantic import BaseModel

from .auth_dependencies import (
    get_current_user,
)

from .mcp_client import (
    call_tool,
    set_mcp_user,
    reset_mcp_user,
)


router = APIRouter(
    prefix="/database",
    tags=["Database"],
)


class DatabaseConnectionRequest(
    BaseModel
):

    database_url: str


# ============================================================
# MCP RESPONSE
# ============================================================

def extract_mcp_response(
    response,
):

    if (
        not response
        or not hasattr(
            response,
            "content",
        )
        or not response.content
    ):

        raise ValueError(
            "Invalid or empty MCP response."
        )

    content = (
        response.content[0]
    )

    text = (
        content.text
        if hasattr(
            content,
            "text",
        )
        else str(content)
    )

    return json.loads(
        text
    )


# ============================================================
# TEST DATABASE CONNECTION
# ============================================================

@router.post(
    "/test-connection"
)
async def test_database_connection(
    data: DatabaseConnectionRequest,
    user=Depends(
        get_current_user
    ),
):

    database_url = (
        data.database_url.strip()
    )

    if not database_url:

        raise HTTPException(
            400,
            "Database URL is required.",
        )

    token = set_mcp_user(
        user["id"]
    )

    connection_id = None

    try:

        result = extract_mcp_response(
            await call_tool(
                "connect_database",
                {
                    "database_url":
                        database_url
                },
            )
        )

        if not result.get(
            "success"
        ):

            raise HTTPException(
                400,
                result.get(
                    "error",
                    "Database connection failed.",
                ),
            )

        connection_id = (
            result.get(
                "connection_id"
            )
        )

        return {

            "success":
                True,

            "message":
                "Database connection test successful.",

            "database_name":
                result.get(
                    "database_name"
                ),

            "host":
                result.get(
                    "host"
                ),

            "version":
                result.get(
                    "version"
                ),
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            500,
            "Failed to test database connection.",
        )

    finally:

        if connection_id:

            try:

                await call_tool(
                    "disconnect_database",
                    {
                        "connection_id":
                            connection_id
                    },
                )

            except Exception:

                pass

        reset_mcp_user(
            token
        )


# ============================================================
# CONNECT DATABASE
# ============================================================

@router.post(
    "/connect"
)
async def connect_database(
    data: DatabaseConnectionRequest,
    user=Depends(
        get_current_user
    ),
):

    database_url = (
        data.database_url.strip()
    )

    if not database_url:

        raise HTTPException(
            400,
            "Database URL is required.",
        )

    token = set_mcp_user(
        user["id"]
    )

    try:

        result = extract_mcp_response(
            await call_tool(
                "connect_database",
                {
                    "database_url":
                        database_url
                },
            )
        )

        if not result.get(
            "success"
        ):

            raise HTTPException(
                400,
                result.get(
                    "error",
                    "Failed to connect database.",
                ),
            )

        return result

    except HTTPException:

        raise

    except Exception as error:

        print("DATABASE CONNECT ERROR:", repr(error))

        raise HTTPException(
            500,
            detail=f"Failed to connect to the database: {error}",
    )

    finally:

        reset_mcp_user(
            token
        )


# ============================================================
# CURRENT CONNECTION
# ============================================================

@router.get(
    "/current/{connection_id}"
)
async def current_database_connection(
    connection_id: str,
    user=Depends(
        get_current_user
    ),
):

    if not connection_id:

        raise HTTPException(
            400,
            "Connection ID is required.",
        )

    token = set_mcp_user(
        user["id"]
    )

    try:

        result = extract_mcp_response(
            await call_tool(
                "current_database_connection",
                {
                    "connection_id":
                        connection_id
                },
            )
        )

        if not result.get(
            "success"
        ):

            # The frontend should not interpret
            # every MCP failure as an explicit disconnect.

            raise HTTPException(
                404,
                "Database connection is no longer available.",
            )

        return result

    except HTTPException:

        raise

    except Exception:

        raise HTTPException(
            503,
            "Database connection verification temporarily failed.",
        )

    finally:

        reset_mcp_user(
            token
        )


# ============================================================
# DISCONNECT
# ============================================================

@router.post(
    "/disconnect/{connection_id}"
)
async def disconnect_database(
    connection_id: str,
    user=Depends(
        get_current_user
    ),
):

    token = set_mcp_user(
        user["id"]
    )

    try:

        result = extract_mcp_response(
            await call_tool(
                "disconnect_database",
                {
                    "connection_id":
                        connection_id
                },
            )
        )

        if not result.get(
            "success"
        ):

            raise HTTPException(
                400,
                result.get(
                    "error",
                    "Failed to disconnect database.",
                ),
            )

        return result

    except HTTPException:

        raise

    except Exception:

        raise HTTPException(
            500,
            "Failed to disconnect database.",
        )

    finally:

        reset_mcp_user(
            token
        )