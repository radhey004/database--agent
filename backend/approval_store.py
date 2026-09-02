import json
import uuid

import psycopg2

from .config import (
    AUTH_DATABASE_URL,
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_approval_db():

    if not AUTH_DATABASE_URL:

        raise RuntimeError(
            "AUTH_DATABASE_URL is not configured."
        )

    return psycopg2.connect(
        AUTH_DATABASE_URL
    )


# ============================================================
# INITIALIZE APPROVAL TABLE
# ============================================================

def init_approval_store():

    conn = get_approval_db()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS approval_requests (

                id UUID PRIMARY KEY,

                user_id UUID NOT NULL
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                connection_id TEXT NOT NULL,

                question TEXT NOT NULL,

                sql TEXT NOT NULL,

                preview JSONB NOT NULL,

                status VARCHAR(20) NOT NULL
                    DEFAULT 'pending',

                created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                CONSTRAINT
                    approval_requests_status_check
                CHECK (
                    status IN (
                        'pending',
                        'approved',
                        'rejected',
                        'failed'
                    )
                )
            );
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_approval_requests_user_id
            ON approval_requests(user_id);
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_approval_requests_status
            ON approval_requests(status);
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_approval_requests_connection_id
            ON approval_requests(connection_id);
            """
        )

        conn.commit()

        cur.close()

    finally:

        conn.close()


# ============================================================
# CREATE APPROVAL REQUEST
# ============================================================

def create_approval_request(
    user_id: str,
    connection_id: str,
    question: str,
    sql: str,
    preview: dict,
):

    if not user_id:

        raise ValueError(
            "User ID is required."
        )

    if not connection_id:

        raise ValueError(
            "Connection ID is required."
        )

    if not sql:

        raise ValueError(
            "SQL is required."
        )

    request_id = uuid.uuid4()

    conn = get_approval_db()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO approval_requests (
                id,
                user_id,
                connection_id,
                question,
                sql,
                preview,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'pending'
            )
            RETURNING
                id,
                user_id,
                connection_id,
                question,
                sql,
                preview,
                status,
                created_at,
                updated_at;
            """,
            (
                str(request_id),
                str(user_id),
                str(connection_id),
                question,
                sql,
                json.dumps(
                    preview,
                    default=str,
                ),
            ),
        )

        row = cur.fetchone()

        conn.commit()

        cur.close()

        return _row_to_dict(
            row
        )

    finally:

        conn.close()


# ============================================================
# GET PENDING REQUEST FOR USER
# ============================================================

def get_pending_approval(
    request_id: str,
    user_id: str,
):

    conn = get_approval_db()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                user_id,
                connection_id,
                question,
                sql,
                preview,
                status,
                created_at,
                updated_at
            FROM approval_requests
            WHERE
                id = %s
                AND user_id = %s
                AND status = 'pending';
            """,
            (
                request_id,
                str(user_id),
            ),
        )

        row = cur.fetchone()

        cur.close()

        if not row:

            return None

        return _row_to_dict(
            row
        )

    finally:

        conn.close()


# ============================================================
# GET APPROVAL REQUEST
# ============================================================

def get_approval_request(
    request_id: str,
):

    conn = get_approval_db()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                user_id,
                connection_id,
                question,
                sql,
                preview,
                status,
                created_at,
                updated_at
            FROM approval_requests
            WHERE id = %s;
            """,
            (
                request_id,
            ),
        )

        row = cur.fetchone()

        cur.close()

        if not row:

            return None

        return _row_to_dict(
            row
        )

    finally:

        conn.close()


# ============================================================
# CLAIM APPROVAL REQUEST
# ============================================================

def claim_approval_request(
    request_id: str,
    user_id: str,
):

    """
    Atomically changes a pending request to approved.

    This prevents two simultaneous approve requests
    from executing the same SQL twice.
    """

    conn = get_approval_db()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            UPDATE approval_requests
            SET
                status = 'approved',
                updated_at = NOW()
            WHERE
                id = %s
                AND user_id = %s
                AND status = 'pending'
            RETURNING
                id,
                user_id,
                connection_id,
                question,
                sql,
                preview,
                status,
                created_at,
                updated_at;
            """,
            (
                request_id,
                str(user_id),
            ),
        )

        row = cur.fetchone()

        if not row:

            conn.rollback()

            return None

        conn.commit()

        cur.close()

        return _row_to_dict(
            row
        )

    finally:

        conn.close()


# ============================================================
# MARK REQUEST FAILED
# ============================================================

def mark_approval_failed(
    request_id: str,
    user_id: str,
):

    conn = get_approval_db()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            UPDATE approval_requests
            SET
                status = 'failed',
                updated_at = NOW()
            WHERE
                id = %s
                AND user_id = %s
                AND status = 'approved';
            """,
            (
                request_id,
                str(user_id),
            ),
        )

        conn.commit()

        cur.close()

    finally:

        conn.close()


# ============================================================
# REJECT APPROVAL
# ============================================================

def reject_approval_request(
    request_id: str,
    user_id: str,
):

    conn = get_approval_db()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            UPDATE approval_requests
            SET
                status = 'rejected',
                updated_at = NOW()
            WHERE
                id = %s
                AND user_id = %s
                AND status = 'pending'
            RETURNING
                id,
                user_id,
                connection_id,
                question,
                sql,
                preview,
                status,
                created_at,
                updated_at;
            """,
            (
                request_id,
                str(user_id),
            ),
        )

        row = cur.fetchone()

        if not row:

            conn.rollback()

            return None

        conn.commit()

        cur.close()

        return _row_to_dict(
            row
        )

    finally:

        conn.close()


# ============================================================
# LIST USER APPROVALS
# ============================================================

def get_user_approvals(
    user_id: str,
    status: str | None = None,
):

    conn = get_approval_db()

    try:

        cur = conn.cursor()

        if status:

            cur.execute(
                """
                SELECT
                    id,
                    user_id,
                    connection_id,
                    question,
                    sql,
                    preview,
                    status,
                    created_at,
                    updated_at
                FROM approval_requests
                WHERE
                    user_id = %s
                    AND status = %s
                ORDER BY
                    created_at DESC;
                """,
                (
                    str(user_id),
                    status,
                ),
            )

        else:

            cur.execute(
                """
                SELECT
                    id,
                    user_id,
                    connection_id,
                    question,
                    sql,
                    preview,
                    status,
                    created_at,
                    updated_at
                FROM approval_requests
                WHERE
                    user_id = %s
                ORDER BY
                    created_at DESC;
                """,
                (
                    str(user_id),
                ),
            )

        rows = cur.fetchall()

        cur.close()

        return [
            _row_to_dict(
                row
            )
            for row in rows
        ]

    finally:

        conn.close()


# ============================================================
# ROW CONVERSION
# ============================================================

def _row_to_dict(
    row,
):

    if not row:

        return None

    preview = row[5]

    if isinstance(
        preview,
        str,
    ):

        try:

            preview = json.loads(
                preview
            )

        except json.JSONDecodeError:

            pass

    return {

        "id":
            str(row[0]),

        "user_id":
            str(row[1]),

        "connection_id":
            str(row[2]),

        "question":
            row[3],

        "sql":
            row[4],

        "preview":
            preview,

        "status":
            row[6],

        "created_at":
            row[7].isoformat(),

        "updated_at":
            row[8].isoformat(),
    }