import json

from fastapi import (
    APIRouter,
    HTTPException,
)

from pydantic import (
    BaseModel,
)

from .mcp_client import (
    call_tool,
)


router = APIRouter(
    prefix="/database",
    tags=["Database"],
)


class DatabaseConnectionRequest(
    BaseModel
):

    database_url: str


def extract_mcp_response(
    response,
):

    print(
        "Raw MCP response:",
        response,
    )

    if not response:

        raise ValueError(
            "Empty response from MCP server."
        )


    if not hasattr(
        response,
        "content",
    ):

        raise ValueError(
            f"Invalid MCP response: {response}"
        )


    if not response.content:

        raise ValueError(
            "MCP server returned empty content."
        )


    content = response.content[0]

    print(
        "MCP content:",
        content,
    )


    if hasattr(
        content,
        "text",
    ):

        text = content.text

    elif isinstance(
        content,
        str,
    ):

        text = content

    else:

        text = str(
            content
        )


    print(
        "MCP response text:",
        repr(text),
    )


    if not text:

        raise ValueError(
            "MCP response text is empty."
        )


    return json.loads(
        text
    )


@router.post(
    "/connect"
)
async def connect_database(
    data: DatabaseConnectionRequest,
):

    database_url = (
        data.database_url.strip()
    )


    if not database_url:

        raise HTTPException(
            status_code=400,
            detail=(
                "Database URL is required."
            ),
        )


    try:

        response = await call_tool(
            "connect_database",
            {
                "database_url":
                    database_url,
            },
        )


        result = (
            extract_mcp_response(
                response
            )
        )


        if not result.get(
            "success"
        ):

            raise HTTPException(
                status_code=400,
                detail=result.get(
                    "error",
                    "Failed to connect database.",
                ),
            )


        return {

            "success": True,

            "message":
                result.get(
                    "message",
                    "Database connected successfully.",
                ),

            "connection_id":
                result.get(
                    "connection_id"
                ),

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

        print(
            "Database connection error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to connect "
                "to the database."
            ),
        )


@router.post(
    "/disconnect/{connection_id}"
)
async def disconnect_database(
    connection_id: str,
):

    try:

        response = await call_tool(
            "disconnect_database",
            {
                "connection_id":
                    connection_id,
            },
        )


        result = (
            extract_mcp_response(
                response
            )
        )


        if not result.get(
            "success"
        ):

            raise HTTPException(
                status_code=400,
                detail=result.get(
                    "error",
                    "Failed to disconnect database.",
                ),
            )


        return {

            "success": True,

            "message":
                result.get(
                    "message",
                    "Database disconnected successfully.",
                ),
        }


    except HTTPException:

        raise


    except Exception as error:

        print(
            "Database disconnect error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to disconnect "
                "database."
            ),
        )


@router.post(
    "/test-connection"
)
async def test_connection(
    data: DatabaseConnectionRequest,
):

    database_url = (
        data.database_url.strip()
    )


    if not database_url:

        raise HTTPException(
            status_code=400,
            detail=(
                "Database URL is required."
            ),
        )


    connection_id = None


    try:

        response = await call_tool(
            "connect_database",
            {
                "database_url":
                    database_url,
            },
        )


        result = (
            extract_mcp_response(
                response
            )
        )


        if not result.get(
            "success"
        ):

            raise HTTPException(
                status_code=400,
                detail=result.get(
                    "error",
                    "Database connection failed.",
                ),
            )


        connection_id = result.get(
            "connection_id"
        )


        return {

            "success": True,

            "message":
                result.get(
                    "message",
                    "Database connected successfully.",
                ),

            "version":
                result.get(
                    "version"
                ),
        }


    except HTTPException:

        raise


    except Exception as error:

        print(
            "Database test error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to test "
                "database connection."
            ),
        )


    finally:

        if connection_id:

            try:

                await call_tool(
                    "disconnect_database",
                    {
                        "connection_id":
                            connection_id,
                    },
                )

            except Exception as error:

                print(
                    "Cleanup error:",
                    repr(error),
                )