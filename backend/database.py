import re
import time
import uuid

from urllib.parse import urlparse

import psycopg2

from psycopg2 import pool

from .sql_validator import (
    validate_read_sql,
    validate_write_sql,
)


MAX_ROWS = 100

SESSION_TTL_SECONDS = 60 * 60


class ConnectionManager:

    def __init__(self):

        self.connections = {}


    def create_connection(
        self,
        database_url: str,
    ):

        self.cleanup_expired()

        connection_id = str(
            uuid.uuid4()
        )

        connection_pool = (
            pool.SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                dsn=database_url,
            )
        )

        conn = None

        try:

            conn = (
                connection_pool.getconn()
            )

            cursor = conn.cursor()

            cursor.execute(
                "SELECT version();"
            )

            version = (
                cursor.fetchone()[0]
            )

            cursor.close()

        except Exception:

            connection_pool.closeall()

            raise

        finally:

            if conn:

                connection_pool.putconn(
                    conn
                )


        parsed = urlparse(
            database_url
        )

        database_name = (
            parsed.path.lstrip("/")
        )

        host = parsed.hostname


        self.connections[
            connection_id
        ] = {
            "pool":
                connection_pool,

            "created_at":
                time.time(),

            "last_used":
                time.time(),

            "database_name":
                database_name,

            "host":
                host,

            "version":
                version,
        }


        return {
            "connection_id":
                connection_id,

            "database_name":
                database_name,

            "host":
                host,

            "version":
                version,
        }


    def get_connection_pool(
        self,
        connection_id: str,
    ):

        self.cleanup_expired()

        session = (
            self.connections.get(
                connection_id
            )
        )

        if not session:

            raise ValueError(
                "Database connection not found "
                "or expired."
            )

        session[
            "last_used"
        ] = time.time()

        return session[
            "pool"
        ]


    def disconnect(
        self,
        connection_id: str,
    ):

        session = (
            self.connections.pop(
                connection_id,
                None,
            )
        )

        if not session:

            raise ValueError(
                "Database connection not found "
                "or already disconnected."
            )

        session[
            "pool"
        ].closeall()


    def cleanup_expired(
        self,
    ):

        now = time.time()

        expired_ids = []


        for (
            connection_id,
            session,
        ) in self.connections.items():

            inactive_for = (
                now
                - session[
                    "last_used"
                ]
            )

            if (
                inactive_for
                > SESSION_TTL_SECONDS
            ):

                expired_ids.append(
                    connection_id
                )


        for connection_id in expired_ids:

            session = (
                self.connections.pop(
                    connection_id,
                    None,
                )
            )

            if session:

                session[
                    "pool"
                ].closeall()


connection_manager = (
    ConnectionManager()
)


def get_connection(
    connection_id: str,
):

    connection_pool = (
        connection_manager
        .get_connection_pool(
            connection_id
        )
    )

    conn = (
        connection_pool.getconn()
    )

    return (
        connection_pool,
        conn,
    )


def release_connection(
    connection_pool,
    conn,
):

    connection_pool.putconn(
        conn
    )


def get_schema(
    connection_id: str,
):

    connection_pool, conn = (
        get_connection(
            connection_id
        )
    )

    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                c.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                CASE
                    WHEN tc.constraint_type = 'PRIMARY KEY'
                    THEN true
                    ELSE false
                END AS is_primary_key

            FROM information_schema.columns c

            LEFT JOIN
                information_schema.key_column_usage kcu

                ON c.table_schema =
                    kcu.table_schema

                AND c.table_name =
                    kcu.table_name

                AND c.column_name =
                    kcu.column_name

            LEFT JOIN
                information_schema.table_constraints tc

                ON kcu.constraint_name =
                    tc.constraint_name

                AND kcu.table_schema =
                    tc.table_schema

                AND kcu.table_name =
                    tc.table_name

            WHERE
                c.table_schema = 'public'

            ORDER BY
                c.table_name,
                c.ordinal_position;
        """)

        rows = cur.fetchall()

        schema = {}


        for (
            table,
            column,
            data_type,
            nullable,
            default,
            primary_key,
        ) in rows:

            if table not in schema:

                schema[table] = {
                    "columns": []
                }


            schema[
                table
            ]["columns"].append({

                "name":
                    column,

                "type":
                    data_type,

                "nullable":
                    nullable == "YES",

                "default":
                    default,

                "primary_key":
                    bool(primary_key),
            })


        return schema

    finally:

        cur.close()

        release_connection(
            connection_pool,
            conn,
        )


def execute_query(
    connection_id: str,
    query: str,
):

    query = validate_read_sql(
        query
    )

    connection_pool, conn = (
        get_connection(
            connection_id
        )
    )

    cur = conn.cursor()

    try:

        cur.execute(
            query
        )

        if cur.description is None:

            raise ValueError(
                "Query did not return any data."
            )


        columns = [

            column[0]

            for column
            in cur.description
        ]


        rows = cur.fetchmany(
            MAX_ROWS
        )


        return [

            dict(
                zip(
                    columns,
                    row,
                )
            )

            for row
            in rows
        ]

    finally:

        cur.close()

        release_connection(
            connection_pool,
            conn,
        )


def _get_operation(
    query: str,
):

    normalized = " ".join(
        query.upper().split()
    )


    for operation in (

        "INSERT",
        "UPDATE",
        "DELETE",
        "CREATE",
        "ALTER",
        "DROP",

    ):

        if normalized.startswith(
            operation
        ):

            return operation


    return "MODIFICATION"


def _get_target(
    query: str,
):

    patterns = [

        r"\bUPDATE\s+"
        r"([a-zA-Z_][\w.]*)",

        r"\bDELETE\s+FROM\s+"
        r"([a-zA-Z_][\w.]*)",

        r"\bINSERT\s+INTO\s+"
        r"([a-zA-Z_][\w.]*)",

        r"\bCREATE\s+TABLE\s+"
        r"(?:IF\s+NOT\s+EXISTS\s+)?"
        r"([a-zA-Z_][\w.]*)",

        r"\bALTER\s+TABLE\s+"
        r"([a-zA-Z_][\w.]*)",

        r"\bDROP\s+TABLE\s+"
        r"(?:IF\s+EXISTS\s+)?"
        r"([a-zA-Z_][\w.]*)",
    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            query,
            re.IGNORECASE,
        )

        if match:

            return match.group(
                1
            )


    return None


def preview_modification(
    connection_id: str,
    query: str,
):

    validate_write_sql(
        query
    )

    return {

        "operation":
            _get_operation(
                query
            ),

        "target":
            _get_target(
                query
            ),

        "query":
            query,

        "connection_id":
            connection_id,
    }


def execute_modification(
    connection_id: str,
    query: str,
):

    query = validate_write_sql(
        query
    )

    connection_pool, conn = (
        get_connection(
            connection_id
        )
    )

    cur = conn.cursor()

    try:

        cur.execute(
            query
        )

        affected_rows = (
            cur.rowcount
        )

        conn.commit()


        return {

            "success":
                True,

            "operation":
                _get_operation(
                    query
                ),

            "target":
                _get_target(
                    query
                ),

            "affected_rows":
                affected_rows,
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        cur.close()

        release_connection(
            connection_pool,
            conn,
        )