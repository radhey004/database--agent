import json
import logging

from mcp.server.mcpserver import (
    MCPServer,
)

from .database import (
    connection_manager,
    get_schema,
    execute_query,
    preview_modification as preview_modification_db,
    execute_modification,
)

from .sql_validator import (
    validate_read_sql,
    validate_write_sql,
)


logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(
    "database-mcp"
)


mcp = MCPServer(
    "Database Server"
)


def success(
    data,
):

    return json.dumps(
        {
            "success": True,
            **data,
        },
        default=str,
    )


def failure(
    error,
    query=None,
):

    return json.dumps(
        {
            "success": False,

            "error":
                str(error),

            "error_type":
                type(error).__name__,

            "retryable":
                True,

            **(
                {
                    "query": query
                }
                if query
                else {}
            ),
        },
        default=str,
    )


@mcp.tool()
def connect_database(
    database_url: str,
) -> str:
    """
    Create a PostgreSQL connection session.

    Returns only a connection ID and
    safe database metadata.
    """

    try:

        result = (
            connection_manager
            .create_connection(
                database_url
            )
        )

        return success({

            "message":
                "Database connected successfully.",

            **result,
        })

    except Exception as error:

        logger.exception(
            "Database connection failed"
        )

        return failure(
            error
        )


@mcp.tool()
def disconnect_database(
    connection_id: str,
) -> str:
    """
    Destroy the PostgreSQL connection
    session associated with this ID.
    """

    try:

        connection_manager.disconnect(
            connection_id
        )

        return success({

            "message":
                "Database disconnected successfully.",
        })

    except Exception as error:

        logger.exception(
            "Database disconnect failed"
        )

        return failure(
            error
        )


@mcp.tool()
def database_schema(
    connection_id: str,
) -> str:
    """
    Discover the schema of the user's
    connected PostgreSQL database.
    """

    try:

        schema = get_schema(
            connection_id
        )

        return success({

            "schema":
                schema,
        })

    except Exception as error:

        logger.exception(
            "Schema discovery failed"
        )

        return failure(
            error
        )


@mcp.tool()
def run_sql(
    connection_id: str,
    query: str,
) -> str:
    """
    Execute one validated read-only
    SQL query.
    """

    try:

        validate_read_sql(
            query
        )

        rows = execute_query(
            connection_id,
            query,
        )

        return success({

            "query":
                query,

            "row_count":
                len(rows),

            "rows":
                rows,
        })

    except Exception as error:

        logger.exception(
            "SQL execution failed"
        )

        return failure(
            error,
            query,
        )


@mcp.tool()
def preview_modification(
    connection_id: str,
    query: str,
) -> str:
    """
    Preview a write operation without
    executing it.
    """

    try:

        validate_write_sql(
            query
        )

        preview = (
            preview_modification_db(
                connection_id,
                query,
            )
        )

        return success({

            "query":
                query,

            "preview":
                preview,
        })

    except Exception as error:

        logger.exception(
            "Modification preview failed"
        )

        return failure(
            error,
            query,
        )


@mcp.tool()
def run_modification(
    connection_id: str,
    query: str,
) -> str:
    """
    Execute an approved database
    modification.
    """

    try:

        validate_write_sql(
            query
        )

        result = (
            execute_modification(
                connection_id,
                query,
            )
        )

        return success({

            "query":
                query,

            "result":
                result,
        })

    except Exception as error:

        logger.exception(
            "Modification execution failed"
        )

        return failure(
            error,
            query,
        )


@mcp.tool()
def database_health(
    connection_id: str,
) -> str:
    """
    Check whether a database session
    is still active.
    """

    try:

        connection_manager.get_connection_pool(
            connection_id
        )

        return success({

            "status":
                "healthy",
        })

    except Exception as error:

        return failure(
            error
        )


if __name__ == "__main__":

    mcp.run(

        transport="streamable-http",

        host="127.0.0.1",

        port=9000,

        stateless_http=True,

        json_response=True,
    )