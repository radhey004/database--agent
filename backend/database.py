import psycopg2
from .config import DATABASE_URL
from .sql_validator import validate_sql

def get_connection():
    return psycopg2.connect(
        DATABASE_URL,
        connect_timeout=10
    )


def get_schema():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        rows = cur.fetchall()

        schema = {}
        for table, column in rows:
            schema.setdefault(table, []).append(column)

        return schema
    finally:
        cur.close()
        conn.close()


def execute_query(query):

    # AST-based SQL validation.
    query = validate_sql(query)

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

        # Maximum 100 rows.
        rows = cur.fetchmany(100)

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    finally:
        cur.close()
        conn.close()
