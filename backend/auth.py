import datetime
import uuid
import bcrypt
import jwt
import psycopg2

from .config import (
    AUTH_DATABASE_URL,
    JWT_ALGORITHM,
    JWT_EXPIRE_DAYS,
    JWT_SECRET_KEY,
    TERMS_VERSION,
)


class AuthenticationError(
    Exception
):
    pass


# ============================================================
# DATABASE
# ============================================================

def get_auth_connection():

    if not AUTH_DATABASE_URL:

        raise RuntimeError(
            "AUTH_DATABASE_URL is not configured."
        )

    return psycopg2.connect(
        AUTH_DATABASE_URL
    )


# ============================================================
# INITIALIZE AUTH DATABASE
# ============================================================

def init_auth_database():

    conn = get_auth_connection()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (

                id UUID PRIMARY KEY,

                email VARCHAR(320)
                    UNIQUE NOT NULL,

                password_hash TEXT
                    NOT NULL,

                terms_version VARCHAR(50)
                    NOT NULL,

                terms_accepted_at TIMESTAMPTZ
                    NOT NULL,

                created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
            );
            """
        )

        conn.commit()

        cur.close()

    finally:

        conn.close()

# ============================================================
# PASSWORD
# ============================================================

def hash_password(
    password: str,
) -> str:

    password_bytes = (
        password.encode(
            "utf-8"
        )
    )

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(
            rounds=12
        ),
    )

    return hashed.decode(
        "utf-8"
    )


def verify_password(
    password: str,
    password_hash: str,
) -> bool:

    try:

        return bcrypt.checkpw(

            password.encode(
                "utf-8"
            ),

            password_hash.encode(
                "utf-8"
            ),
        )

    except (
        ValueError,
        TypeError,
    ):

        return False


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    email: str,
    password: str,
) -> dict:

    normalized_email = (
        email.strip().lower()
    )

    password_hash = (
        hash_password(
            password
        )
    )

    user_id = uuid.uuid4()

    conn = get_auth_connection()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO users (
                id,
                email,
                password_hash,
                terms_version,
                terms_accepted_at
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                NOW()
            )
            RETURNING
                id,
                email,
                terms_version,
                terms_accepted_at,
                created_at;
            """,
            (
                str(user_id),
                normalized_email,
                password_hash,
                TERMS_VERSION,
            ),
        )

        row = cur.fetchone()

        conn.commit()

        cur.close()

        return {
            "id": str(row[0]),
            "email": row[1],
            "terms_version": row[2],
            "terms_accepted_at":
                row[3].isoformat(),
            "created_at":
                row[4].isoformat(),
        }

    except psycopg2.errors.UniqueViolation:

        conn.rollback()

        raise AuthenticationError(
            "An account with this email already exists."
        )

    finally:

        conn.close()


# ============================================================
# FIND USER
# ============================================================

def get_user_by_email(
    email: str,
):

    normalized_email = (
        email.strip().lower()
    )

    conn = get_auth_connection()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                email,
                password_hash,
                terms_version,
                terms_accepted_at,
                created_at
            FROM users
            WHERE email = %s;
            """,
            (
                normalized_email,
            ),
        )

        row = cur.fetchone()

        cur.close()

        if not row:

            return None

        return {
            "id": str(row[0]),
            "email": row[1],
            "password_hash":
                row[2],
            "terms_version":
                row[3],
            "terms_accepted_at":
                row[4],
            "created_at":
                row[5],
        }

    finally:

        conn.close()


# ============================================================
# FIND USER BY ID
# ============================================================

def get_user_by_id(
    user_id: str,
):

    conn = get_auth_connection()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                email,
                terms_version,
                terms_accepted_at,
                created_at
            FROM users
            WHERE id = %s;
            """,
            (
                user_id,
            ),
        )

        row = cur.fetchone()

        cur.close()

        if not row:

            return None

        return {
            "id": str(row[0]),
            "email": row[1],
            "terms_version":
                row[2],
            "terms_accepted_at":
                row[3],
            "created_at":
                row[4],
        }

    finally:

        conn.close()


# ============================================================
# JWT
# ============================================================

def create_access_token(
    user_id: str,
):

    now = datetime.datetime.now(
        datetime.timezone.utc
    )

    expires_at = (
        now
        + datetime.timedelta(
            days=JWT_EXPIRE_DAYS
        )
    )

    payload = {

        "sub":
            str(user_id),

        "iat":
            int(
                now.timestamp()
            ),

        "exp":
            int(
                expires_at.timestamp()
            ),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(
    token: str,
):

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[
                JWT_ALGORITHM
            ],
        )

    except jwt.ExpiredSignatureError:

        raise AuthenticationError(
            "Authentication session has expired."
        )

    except jwt.InvalidTokenError:

        raise AuthenticationError(
            "Invalid authentication session."
        )

    user_id = payload.get(
        "sub"
    )

    if not user_id:

        raise AuthenticationError(
            "Invalid authentication session."
        )

    return user_id


# ============================================================
# LOGIN
# ============================================================

def authenticate_user(
    email: str,
    password: str,
):

    user = get_user_by_email(
        email
    )

    if not user:

        raise AuthenticationError(
            "Invalid email or password."
        )

    if not verify_password(
        password,
        user["password_hash"],
    ):

        raise AuthenticationError(
            "Invalid email or password."
        )

    return user