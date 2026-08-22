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
    "COPY",
    "CREATE DATABASE",
    "DROP DATABASE",
    "ALTER DATABASE",
    "CREATE EXTENSION",
)


ALLOWED_DROP_OBJECTS = (
    "TABLE",
    "VIEW",
    "INDEX",
    "SCHEMA",
)


DANGEROUS_FUNCTIONS = {
    "pg_read_file",
    "pg_write_file",
    "pg_ls_dir",
    "lo_import",
    "lo_export",
    "dblink_connect",
}


def parse_single_statement(
    query: str,
):

    query = query.strip()

    if not query:

        raise ValueError(
            "SQL query is empty."
        )

    try:

        statements = sqlglot.parse(
            query,
            dialect="postgres",
        )

    except Exception as error:

        raise ValueError(
            f"Invalid SQL syntax: {error}"
        ) from error

    if len(statements) != 1:

        raise ValueError(
            "Only one SQL statement is allowed."
        )

    return query, statements[0]


def check_blocked_command(
    query: str,
):

    normalized = " ".join(
        query.upper().split()
    )

    for command in BLOCKED_PREFIXES:

        if (
            normalized == command
            or normalized.startswith(
                command + " "
            )
        ):

            raise ValueError(
                f"SQL command is not allowed: "
                f"{command}"
            )


def check_dangerous_functions(
    ast,
):

    for node in ast.walk():

        if isinstance(
            node,
            exp.Func,
        ):

            function_name = (
                node.sql_name()
                .lower()
            )

            if function_name in (
                DANGEROUS_FUNCTIONS
            ):

                raise ValueError(
                    "Dangerous PostgreSQL "
                    f"function is not allowed: "
                    f"{function_name}"
                )


def validate_read_sql(
    query: str,
) -> str:

    query, ast = parse_single_statement(
        query
    )

    check_blocked_command(
        query
    )

    check_dangerous_functions(
        ast
    )

    if not isinstance(
        ast,
        READ_TYPES,
    ):

        raise ValueError(
            "Only SELECT queries are "
            "allowed for read operations."
        )

    return query


def validate_write_sql(
    query: str,
) -> str:

    query, ast = parse_single_statement(
        query
    )

    check_blocked_command(
        query
    )

    check_dangerous_functions(
        ast
    )

    if not isinstance(
        ast,
        WRITE_TYPES,
    ):

        raise ValueError(
            "Only INSERT, UPDATE, DELETE, "
            "CREATE, ALTER or DROP queries "
            "are allowed."
        )

    if isinstance(
        ast,
        exp.Drop,
    ):

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
                "DROP INDEX or DROP SCHEMA "
                "are allowed."
            )

    return query


def validate_schema_usage(
    query: str,
    schema: dict,
):
    """
    Verify that referenced tables and columns
    exist in the discovered schema.

    CREATE statements are handled separately
    because the target object may not exist yet.
    """

    _, ast = parse_single_statement(
        query
    )

    # CREATE TABLE / VIEW / INDEX etc.
    # creates a new object, so its target
    # must not be required to already exist.
    if isinstance(
        ast,
        exp.Create,
    ):

        return True

    if not schema:

        raise ValueError(
            "Database schema is empty."
        )

    table_columns = {}

    for table_name, table_data in (
        schema.items()
    ):

        table_columns[
            table_name.lower()
        ] = {
            str(
                column["name"]
            ).lower()

            for column in table_data.get(
                "columns",
                [],
            )
        }

    known_tables = set(
        table_columns.keys()
    )

    referenced_tables = set()

    for table in ast.find_all(
        exp.Table
    ):

        table_name = (
            table.name.lower()
        )

        referenced_tables.add(
            table_name
        )

    unknown_tables = (
        referenced_tables
        - known_tables
    )

    if unknown_tables:

        raise ValueError(
            "Unknown table(s): "
            + ", ".join(
                sorted(
                    unknown_tables
                )
            )
        )

    for column in ast.find_all(
        exp.Column
    ):

        column_name = (
            column.name.lower()
        )

        if column_name == "*":

            continue

        table_name = (
            column.table.lower()
            if column.table
            else None
        )

        if table_name:

            if table_name not in (
                table_columns
            ):

                raise ValueError(
                    f"Unknown table: "
                    f"'{table_name}'"
                )

            if column_name not in (
                table_columns[
                    table_name
                ]
            ):

                raise ValueError(
                    f"Unknown column "
                    f"'{column.name}' in "
                    f"table '{table_name}'"
                )

        else:

            matches = [

                table

                for table, columns
                in table_columns.items()

                if column_name in columns
            ]

            if not matches:

                raise ValueError(
                    f"Unknown column: "
                    f"'{column.name}'"
                )

    return True