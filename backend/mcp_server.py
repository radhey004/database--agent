import json
import logging

from mcp.server.mcpserver import MCPServer

from .database import (
    connection_manager,
    get_schema,
    execute_query,
    preview_modification as preview_modification_db,
    execute_modification,
)

from .mcp_auth import (
    verify_mcp_context,
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


# ============================================================
# RESPONSE HELPERS
# ============================================================

def success(data):

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
                    "query":
                        query
                }
                if query
                else {}
            ),
        },
        default=str,
    )


# ============================================================
# AUTHENTICATION
# ============================================================

def authenticate_mcp_request(
    mcp_context: str,
):

    return verify_mcp_context(
        mcp_context
    )


# ============================================================
# CONNECT DATABASE
# ============================================================

@mcp.tool()
def connect_database(
    database_url: str,
    mcp_context: str,
) -> str:

    try:

        context = (
            authenticate_mcp_request(
                mcp_context
            )
        )

        user_id = (
            context["user_id"]
        )

        result = (
            connection_manager
            .create_connection(
                database_url,
                user_id,
            )
        )

        logger.info(
            "Database connected: user=%s connection=%s",
            user_id,
            result["connection_id"],
        )

        return success(
            {
                "message":
                    "Database connected successfully.",

                "connection_id":
                    result["connection_id"],

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
        )

    except Exception as error:

        logger.exception(
            "Database connection failed"
        )

        return failure(
            error
        )


# ============================================================
# DISCONNECT DATABASE
# ============================================================

@mcp.tool()
def disconnect_database(
    connection_id: str,
    mcp_context: str,
) -> str:

    try:

        context = (
            authenticate_mcp_request(
                mcp_context
            )
        )

        user_id = (
            context["user_id"]
        )

        connection_manager.disconnect(
            connection_id,
            user_id,
        )

        logger.info(
            "Database disconnected: user=%s connection=%s",
            user_id,
            connection_id,
        )

        return success(
            {
                "message":
                    "Database disconnected successfully."
            }
        )

    except Exception as error:

        logger.exception(
            "Database disconnect failed"
        )

        return failure(
            error
        )


# ============================================================
# CURRENT DATABASE CONNECTION
# ============================================================

@mcp.tool()
def current_database_connection(
    connection_id: str,
    mcp_context: str,
) -> str:

    try:

        context = (
            authenticate_mcp_request(
                mcp_context
            )
        )

        user_id = (
            context["user_id"]
        )

        info = (
            connection_manager
            .get_connection_info(
                connection_id,
                user_id,
            )
        )

        return success(
            info
        )

    except Exception as error:

        logger.exception(
            "Current database connection lookup failed"
        )

        return failure(
            error
        )


# ============================================================
# DATABASE SCHEMA
# ============================================================

@mcp.tool()
def database_schema(
    connection_id: str,
    mcp_context: str,
) -> str:

    try:

        context = (
            authenticate_mcp_request(
                mcp_context
            )
        )

        user_id = (
            context["user_id"]
        )

        schema = get_schema(
            connection_id,
            user_id,
        )

        return success(
            {
                "schema":
                    schema
            }
        )

    except Exception as error:

        logger.exception(
            "Schema discovery failed"
        )

        return failure(
            error
        )


# ============================================================
# READ SQL
# ============================================================

@mcp.tool()
def run_sql(
    connection_id: str,
    query: str,
    mcp_context: str,
) -> str:

    try:

        context = (
            authenticate_mcp_request(
                mcp_context
            )
        )

        user_id = (
            context["user_id"]
        )

        validate_read_sql(
            query
        )

        rows = execute_query(
            connection_id,
            query,
            user_id,
        )

        return success(
            {
                "query":
                    query,

                "row_count":
                    len(rows),

                "rows":
                    rows,
            }
        )

    except Exception as error:

        logger.exception(
            "SQL execution failed"
        )

        return failure(
            error,
            query,
        )


# ============================================================
# PREVIEW MODIFICATION
# ============================================================

@mcp.tool()
def preview_modification(
    connection_id: str,
    query: str,
    mcp_context: str,
) -> str:

    try:

        context = (
            authenticate_mcp_request(
                mcp_context
            )
        )

        user_id = (
            context["user_id"]
        )

        validate_write_sql(
            query
        )

        preview = (
            preview_modification_db(
                connection_id,
                query,
                user_id,
            )
        )

        return success(
            {
                "query":
                    query,

                "preview":
                    preview,
            }
        )

    except Exception as error:

        logger.exception(
            "Modification preview failed"
        )

        return failure(
            error,
            query,
        )


# ============================================================
# RUN MODIFICATION
# ============================================================

@mcp.tool()
def run_modification(
    connection_id: str,
    query: str,
    mcp_context: str,
) -> str:

    try:

        context = (
            authenticate_mcp_request(
                mcp_context
            )
        )

        user_id = (
            context["user_id"]
        )

        validate_write_sql(
            query
        )

        result = (
            execute_modification(
                connection_id,
                query,
                user_id,
            )
        )

        return success(
            {
                "query":
                    query,

                "result":
                    result,
            }
        )

    except Exception as error:

        logger.exception(
            "Modification execution failed"
        )

        return failure(
            error,
            query,
        )


# ============================================================
# DATABASE HEALTH
# ============================================================

@mcp.tool()
def database_health(
    connection_id: str,
    mcp_context: str,
) -> str:

    try:

        context = (
            authenticate_mcp_request(
                mcp_context
            )
        )

        user_id = (
            context["user_id"]
        )

        connection_manager.verify_owner(
            connection_id,
            user_id,
        )

        return success(
            {
                "status":
                    "healthy"
            }
        )

    except Exception as error:

        logger.exception(
            "Database health check failed"
        )

        return failure(
            error
        )


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":

    logger.info(
        "Starting stateful Database MCP server..."
    )

    logger.info(
        "Database credentials are held only in memory."
    )

    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=9000,
        stateless_http=False,
        json_response=True,
    )