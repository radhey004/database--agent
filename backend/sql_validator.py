import sqlglot
from sqlglot import exp


def validate_sql(query: str) -> str:
    """
    Allow exactly one PostgreSQL SELECT statement.
    Reject INSERT, UPDATE, DELETE, DROP, ALTER, etc.
    """

    query = query.strip()

    if not query:
        raise ValueError("Empty SQL query")

    try:
        # Parse as PostgreSQL.
        statements = sqlglot.parse(
            query,
            dialect="postgres"
        )
    except Exception as error:
        raise ValueError(
            f"Invalid SQL: {error}"
        )

    # Only one SQL statement is allowed.
    if len(statements) != 1:
        raise ValueError(
            "Only one SQL statement is allowed"
        )

    ast = statements[0]

    # The root must actually be a SELECT.
    if not isinstance(ast, exp.Select):
        raise ValueError(
            "Only SELECT queries are allowed"
        )

    return query