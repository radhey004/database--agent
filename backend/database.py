import time
import uuid

from urllib.parse import (
    urlparse,
)

from psycopg2 import (
    pool,
)
from requests import session


from .sql_validator import (
    validate_read_sql,
    validate_write_sql,
)


# ============================================================
# CONFIGURATION
# ============================================================

MAX_ROWS = 100

SESSION_TTL_SECONDS = (
    24 * 60 * 60
)


# ============================================================
# CONNECTION MANAGER
# ============================================================

class ConnectionManager:

    def __init__(
        self,
    ):

        self.connections = {}


    # ========================================================
    # CREATE CONNECTION
    # ========================================================

    def create_connection(
        self,
        database_url: str,
        user_id: str,
    ):

        self.cleanup_expired()

        if not user_id:

            raise ValueError(
                "User identity is required."
            )

        if not database_url:

            raise ValueError(
                "Database URL is required."
            )

        connection_id = str(
            uuid.uuid4()
        )

        connection_pool = None

        try:

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
                    connection_pool
                    .getconn()
                )

                cursor = (
                    conn.cursor()
                )

                cursor.execute(
                    "SELECT version();"
                )

                version = (
                    cursor
                    .fetchone()[0]
                )

                cursor.close()

            finally:

                if conn:

                    connection_pool.putconn(
                        conn
                    )

        except Exception:

            if connection_pool:

                connection_pool.closeall()

            raise

        parsed = urlparse(
            database_url
        )

        database_name = (
            parsed.path
            .lstrip("/")
        )

        host = (
            parsed.hostname
        )

        now = time.time()

        self.connections[
            connection_id
        ] = {

            "user_id":
                str(user_id),

            "pool":
                connection_pool,

            "created_at":
                now,

            "last_used":
                now,

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


    # ========================================================
    # VERIFY OWNER
    # ========================================================

    def verify_owner(
        self,
        connection_id: str,
        user_id: str,
    ):

        if not user_id:

            raise PermissionError(
                "Authenticated user is required."
            )

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

        if (
            session["user_id"]
            != str(user_id)
        ):

            raise PermissionError(
                "You are not authorized "
                "to use this database connection."
            )

        # Every successful request refreshes
        # the inactivity timer.

        session[
            "last_used"
        ] = time.time()

        return session


    # ========================================================
    # GET CONNECTION INFO
    # ========================================================

    def get_connection_info(
        self,
        connection_id: str,
        user_id: str,
    ):

        session = self.verify_owner(
            connection_id,
            user_id,
        )

        return {

            "connection_id":
                connection_id,

            "database_name":
                session.get(
                    "database_name"
                ),

            "host":
                session.get(
                    "host"
                ),

            "version":
                session.get(
                    "version"
                ),
        }


    # ========================================================
    # GET CONNECTION POOL
    # ========================================================

    def get_connection_pool(
        self,
        connection_id: str,
        user_id: str,
    ):

        session = (
            self.verify_owner(
                connection_id,
                user_id,
            )
        )

        return session["pool"]


    # ========================================================
    # DISCONNECT
    # ========================================================

    def disconnect(
        self,
        connection_id: str,
        user_id: str,
    ):

        session = (
            self.verify_owner(
                connection_id,
                user_id,
            )
        )

        session = (
            self.connections.pop(
                connection_id
            )
        )

        try:

            session[
                "pool"
            ].closeall()

        except Exception:

            pass


    # ========================================================
    # CLEANUP EXPIRED CONNECTIONS
    # ========================================================

    def cleanup_expired(
        self,
    ):

        now = time.time()

        expired_ids = []

        for (
            connection_id,
            session,
        ) in list(
            self.connections.items()
        ):

            inactive_for = (
                now
                - session["last_used"]
            )

            if (
                inactive_for
                > SESSION_TTL_SECONDS
            ):

                expired_ids.append(
                    connection_id
                )

        for connection_id in (
            expired_ids
        ):

            session = (
                self.connections.pop(
                    connection_id,
                    None,
                )
            )

            if session:

                try:

                    session[
                        "pool"
                    ].closeall()

                except Exception:

                    pass


# ============================================================
# GLOBAL CONNECTION MANAGER
# ============================================================

connection_manager = (
    ConnectionManager()
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection(
    connection_id: str,
    user_id: str,
):

    if not user_id:

        raise PermissionError(
            "Authenticated user is required."
        )

    connection_pool = (
        connection_manager
        .get_connection_pool(
            connection_id,
            user_id,
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

    if conn:

        try:

            connection_pool.putconn(
                conn
            )

        except Exception:

            try:

                connection_pool.putconn(
                    conn,
                    close=True,
                )

            except Exception:

                pass


# ============================================================
# GET SCHEMA
# ============================================================

def get_schema(
    connection_id: str,
    user_id: str,
):

    connection_pool, conn = (
        get_connection(
            connection_id,
            user_id,
        )
    )

    cur = None

    try:

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                c.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,

                CASE
                    WHEN EXISTS (
                        SELECT 1

                        FROM
                            information_schema
                            .table_constraints tc

                        JOIN
                            information_schema
                            .key_column_usage kcu

                        ON
                            tc.constraint_name =
                            kcu.constraint_name

                        AND
                            tc.table_schema =
                            kcu.table_schema

                        AND
                            tc.table_name =
                            kcu.table_name

                        WHERE
                            tc.constraint_type =
                            'PRIMARY KEY'

                        AND
                            kcu.table_schema =
                            c.table_schema

                        AND
                            kcu.table_name =
                            c.table_name

                        AND
                            kcu.column_name =
                            c.column_name
                    )

                    THEN true

                    ELSE false

                END AS is_primary_key

            FROM
                information_schema.columns c

            WHERE
                c.table_schema = 'public'

            ORDER BY
                c.table_name,
                c.ordinal_position;
            """
        )

        rows = (
            cur.fetchall()
        )

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

                schema[
                    table
                ] = {

                    "columns":
                        []
                }

            schema[
                table
            ][
                "columns"
            ].append({

                "name":
                    column,

                "type":
                    data_type,

                "nullable":
                    nullable == "YES",

                "default":
                    default,

                "primary_key":
                    bool(
                        primary_key
                    ),
            })

        return schema

    finally:

        if cur:

            cur.close()

        release_connection(
            connection_pool,
            conn,
        )


# ============================================================
# EXECUTE READ QUERY
# ============================================================

def execute_query(
    connection_id: str,
    query: str,
    user_id: str,
):

    query = validate_read_sql(
        query
    )

    connection_pool, conn = (
        get_connection(
            connection_id,
            user_id,
        )
    )

    cur = None

    try:

        cur = conn.cursor()

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

        rows = (
            cur.fetchmany(
                MAX_ROWS
            )
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

        if cur:

            cur.close()

        release_connection(
            connection_pool,
            conn,
        )


# ============================================================
# PREVIEW MODIFICATION
# ============================================================

def preview_modification(
    connection_id: str,
    query: str,
    user_id: str,
):

    query = validate_write_sql(
        query
    )

    connection_pool, conn = (
        get_connection(
            connection_id,
            user_id,
        )
    )

    cur = None

    try:

        cur = conn.cursor()

        # ----------------------------------------------------
        # Use a transaction that is ALWAYS rolled back.
        #
        # This lets PostgreSQL validate and execute the
        # modification without permanently changing data.
        # ----------------------------------------------------

        cur.execute(
            "BEGIN;"
        )

        cur.execute(
            query
        )

        row_count = (
            cur.rowcount
        )

        preview = {

            "operation":
                query
                .split(
                    None,
                    1,
                )[0]
                .upper(),

            "affected_rows":
                row_count,

            "query":
                query,
        }

        conn.rollback()

        return preview

    except Exception:

        try:

            conn.rollback()

        except Exception:

            pass

        raise

    finally:

        if cur:

            cur.close()

        release_connection(
            connection_pool,
            conn,
        )


# ============================================================
# EXECUTE MODIFICATION
# ============================================================

def execute_modification(
    connection_id: str,
    query: str,
    user_id: str,
):

    query = validate_write_sql(
        query
    )

    connection_pool, conn = (
        get_connection(
            connection_id,
            user_id,
        )
    )

    cur = None

    try:

        cur = conn.cursor()

        cur.execute(
            query
        )

        affected_rows = (
            cur.rowcount
        )

        conn.commit()

        return {

            "affected_rows":
                affected_rows,

            "message":
                "Modification executed successfully.",
        }

    except Exception:

        try:

            conn.rollback()

        except Exception:

            pass

        raise

    finally:

        if cur:

            cur.close()

        release_connection(
            connection_pool,
            conn,
        )