import re

import psycopg2

from .config import DATABASE_URL
from .sql_validator import (
    validate_read_sql,
    validate_write_sql,
)


def get_connection():

    return psycopg2.connect(
        DATABASE_URL,
        connect_timeout=10,
    )


def get_schema():

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                table_name,
                column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY
                table_name,
                ordinal_position;
        """)

        rows = cur.fetchall()

        schema = {}

        for table, column in rows:

            schema.setdefault(
                table,
                []
            ).append(column)

        return schema

    finally:

        cur.close()
        conn.close()


def execute_query(query):

    query = validate_read_sql(
        query
    )

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(query)

        if cur.description is None:

            raise ValueError(
                "Query did not return data"
            )

        columns = [
            desc[0]
            for desc in cur.description
        ]

        rows = cur.fetchmany(100)

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    finally:

        cur.close()
        conn.close()


def _get_operation(query: str):

    normalized = " ".join(
        query.upper().split()
    )

    if normalized.startswith("INSERT"):
        return "INSERT"

    if normalized.startswith("UPDATE"):
        return "UPDATE"

    if normalized.startswith("DELETE"):
        return "DELETE"

    if normalized.startswith("CREATE"):
        return "CREATE"

    if normalized.startswith("ALTER"):
        return "ALTER"

    if normalized.startswith("DROP"):
        return "DROP"

    if normalized.startswith("TRUNCATE"):
        return "TRUNCATE"

    return "MODIFICATION"


def _get_target(query: str):

    patterns = [

        r"\bUPDATE\s+([a-zA-Z_][\w.]*)",

        r"\bDELETE\s+FROM\s+([a-zA-Z_][\w.]*)",

        r"\bINSERT\s+INTO\s+([a-zA-Z_][\w.]*)",

        r"\bCREATE\s+TABLE\s+"
        r"(?:IF\s+NOT\s+EXISTS\s+)?"
        r"([a-zA-Z_][\w.]*)",

        r"\bALTER\s+TABLE\s+"
        r"([a-zA-Z_][\w.]*)",

        r"\bDROP\s+TABLE\s+"
        r"(?:IF\s+EXISTS\s+)?"
        r"([a-zA-Z_][\w.]*)",

        r"\bTRUNCATE\s+"
        r"(?:TABLE\s+)?"
        r"([a-zA-Z_][\w.]*)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            query,
            re.IGNORECASE,
        )

        if match:

            return match.group(1)

    return "database"


def _rows_from_cursor(cur):

    if cur.description is None:

        return []

    columns = [
        desc[0]
        for desc in cur.description
    ]

    rows = cur.fetchall()

    return [
        dict(zip(columns, row))
        for row in rows
    ]


def _get_where_clause(query: str):

    match = re.search(
        r"\bWHERE\b(.+?)(?:\s+RETURNING\b|;?$)",
        query,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:

        return None

    return match.group(1).strip()


def _preview_delete(
    query: str,
    table: str,
):

    where = _get_where_clause(
        query
    )

    if not where:

        select_query = (
            f"SELECT * FROM {table}"
        )

    else:

        select_query = (
            f"SELECT * FROM {table} "
            f"WHERE {where}"
        )

    rows = execute_query(
        select_query
    )

    return {
        "operation": "DELETE",
        "target": table,
        "affected_rows": len(rows),
        "rows": rows,
        "preview_only": True,
        "message": (
            "These rows would be deleted "
            "after approval."
        ),
    }


def _preview_update(
    query: str,
    table: str,
):

    match = re.search(
        r"\bUPDATE\s+"
        r"[a-zA-Z_][\w.]*"
        r"\s+SET\s+(.+?)"
        r"\s+WHERE\s+(.+?)"
        r"(?:\s+RETURNING\b.*)?"
        r";?$",
        query,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:

        raise ValueError(
            "UPDATE preview requires a WHERE clause."
        )

    set_clause = match.group(1).strip()
    where_clause = match.group(2).strip()

    before_query = (
        f"SELECT * FROM {table} "
        f"WHERE {where_clause}"
    )

    before_rows = execute_query(
        before_query
    )

    changes = []

    assignments = [
        item.strip()
        for item in set_clause.split(",")
    ]

    for row in before_rows:

        before = dict(row)
        after = dict(row)

        for assignment in assignments:

            parts = assignment.split(
                "=",
                1
            )

            if len(parts) != 2:
                continue

            column = parts[0].strip()
            value = parts[1].strip()

            value_clean = (
                value
                .strip()
                .rstrip(";")
            )

            if (
                value_clean.startswith("'")
                and value_clean.endswith("'")
            ):

                new_value = value_clean[
                    1:-1
                ]

            elif value_clean.upper() == "NULL":

                new_value = None

            else:

                new_value = value_clean

            after[column] = new_value

        changes.append({
            "before": before,
            "after": after,
        })

    return {
        "operation": "UPDATE",
        "target": table,
        "affected_rows": len(before_rows),
        "rows": changes,
        "preview_only": True,
        "message": (
            "These rows would be updated "
            "after approval."
        ),
    }


def _preview_insert(
    query: str,
    table: str,
):

    match = re.search(
        r"\bINSERT\s+INTO\s+"
        r"[a-zA-Z_][\w.]*"
        r"\s*\((.*?)\)"
        r"\s*VALUES\s*\((.*?)\)"
        r"(?:\s+RETURNING\b.*)?"
        r";?$",
        query,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:

        raise ValueError(
            "Unable to preview this INSERT."
        )

    columns = [
        column.strip()
        for column in match.group(1).split(",")
    ]

    values = [
        value.strip()
        for value in match.group(2).split(",")
    ]

    if len(columns) != len(values):

        raise ValueError(
            "INSERT columns and values do not match."
        )

    row = {}

    for column, value in zip(
        columns,
        values,
    ):

        value = (
            value
            .strip()
            .rstrip(";")
        )

        if (
            value.startswith("'")
            and value.endswith("'")
        ):

            value = value[1:-1]

        elif value.upper() == "NULL":

            value = None

        row[column] = value

    return {
        "operation": "INSERT",
        "target": table,
        "affected_rows": 1,
        "rows": [row],
        "preview_only": True,
        "message": (
            "This row would be inserted "
            "after approval."
        ),
    }


def _preview_ddl(
    query: str,
    operation: str,
    target: str,
):

    return {
        "operation": operation,
        "target": target,
        "affected_rows": None,
        "rows": [],
        "preview_only": True,
        "message": (
            f"{operation} operation on "
            f"{target} would be applied "
            "after approval."
        ),
    }


def preview_modification(
    query
):

    query = validate_write_sql(
        query
    )

    operation = _get_operation(
        query
    )

    target = _get_target(
        query
    )

    if operation == "DELETE":

        return _preview_delete(
            query,
            target,
        )

    if operation == "UPDATE":

        return _preview_update(
            query,
            target,
        )

    if operation == "INSERT":

        return _preview_insert(
            query,
            target,
        )

    return _preview_ddl(
        query,
        operation,
        target,
    )


def execute_modification(
    query
):

    query = validate_write_sql(
        query
    )

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(query)

        result = {
            "status": "success",
            "message": (
                "Modification executed "
                "successfully."
            ),
            "row_count": cur.rowcount,
        }

        if cur.description is not None:

            result["rows"] = (
                _rows_from_cursor(cur)
            )

        conn.commit()

        return result

    except Exception:

        conn.rollback()

        raise

    finally:

        cur.close()
        conn.close()