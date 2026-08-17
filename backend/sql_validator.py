import sqlglot
from sqlglot import exp


READ_TYPES = (
    exp.Select,
)

WRITE_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Alter,
    exp.Drop,
)


BLOCKED_PREFIXES = (
    "GRANT",
    "REVOKE",
    "COMMENT",
    "BEGIN",
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    "RELEASE",
    "CREATE EXTENSION",
    "CREATE DATABASE",
    "DROP DATABASE",
    "ALTER DATABASE",
    "COPY",
)


ALLOWED_DROP_OBJECTS = (
    "TABLE",
    "VIEW",
    "INDEX",
    "SCHEMA",
)


def parse_single_statement(query: str):

    query = query.strip()

    if not query:
        raise ValueError(
            "Empty SQL query"
        )

    try:

        statements = sqlglot.parse(
            query,
            dialect="postgres"
        )

    except Exception as error:

        raise ValueError(
            f"Invalid SQL: {error}"
        )

    if len(statements) != 1:

        raise ValueError(
            "Only one SQL statement is allowed"
        )

    return query, statements[0]


def check_blocked_command(query: str):

    normalized = " ".join(
        query.upper().split()
    )

    for command in BLOCKED_PREFIXES:

        if normalized.startswith(command):

            raise ValueError(
                f"SQL command is not allowed: {command}"
            )


def validate_read_sql(query: str) -> str:

    query, ast = parse_single_statement(
        query
    )

    check_blocked_command(query)

    if not isinstance(ast, READ_TYPES):

        raise ValueError(
            "Only SELECT queries are allowed "
            "for read operations"
        )

    return query


def validate_write_sql(query: str) -> str:

    query, ast = parse_single_statement(
        query
    )

    check_blocked_command(query)

    if not isinstance(
        ast,
        WRITE_TYPES
    ):

        raise ValueError(
            "Only DML/DDL modification queries "
            "are allowed"
        )

    # Extra protection for DROP.
    if isinstance(ast, exp.Drop):

        normalized = " ".join(
            query.upper().split()
        )

        if not any(
            normalized.startswith(
                f"DROP {object_type}"
            )
            for object_type
            in ALLOWED_DROP_OBJECTS
        ):

            raise ValueError(
                "Only DROP TABLE, DROP VIEW, "
                "DROP INDEX, or DROP SCHEMA "
                "are allowed"
            )

    return query