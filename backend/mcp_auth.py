import hashlib
import hmac
import json
import time


from .config import (
    MCP_INTERNAL_SECRET,
)


# ============================================================
# CONFIGURATION
# ============================================================

TOKEN_TTL_SECONDS = 60


# ============================================================
# SIGN PAYLOAD
# ============================================================

def _sign(
    payload: str,
) -> str:

    return hmac.new(
        MCP_INTERNAL_SECRET.encode(
            "utf-8"
        ),
        payload.encode(
            "utf-8"
        ),
        hashlib.sha256,
    ).hexdigest()


# ============================================================
# CREATE INTERNAL MCP CONTEXT
# ============================================================

def create_mcp_context(
    user_id: str,
) -> str:

    if not user_id:

        raise ValueError(
            "User ID is required "
            "for MCP context."
        )

    payload = {

        "user_id":
            str(user_id),

        "issued_at":
            int(
                time.time()
            ),
    }

    encoded_payload = json.dumps(
        payload,
        separators=(
            ",",
            ":",
        ),
        sort_keys=True,
    )

    signature = _sign(
        encoded_payload
    )

    envelope = {

        "payload":
            payload,

        "signature":
            signature,
    }

    return json.dumps(
        envelope,
        separators=(
            ",",
            ":",
        ),
    )


# ============================================================
# VERIFY INTERNAL MCP CONTEXT
# ============================================================

def verify_mcp_context(
    token: str,
) -> dict:

    if not token:

        raise ValueError(
            "MCP authentication context "
            "is missing."
        )

    try:

        envelope = json.loads(
            token
        )

        payload = envelope[
            "payload"
        ]

        signature = envelope[
            "signature"
        ]

        encoded_payload = json.dumps(
            payload,
            separators=(
                ",",
                ":",
            ),
            sort_keys=True,
        )

        expected_signature = _sign(
            encoded_payload
        )

        if not hmac.compare_digest(
            signature,
            expected_signature,
        ):

            raise ValueError(
                "Invalid MCP authentication signature."
            )

        issued_at = int(
            payload[
                "issued_at"
            ]
        )

        current_time = int(
            time.time()
        )

        age = (
            current_time
            - issued_at
        )

        if age < 0:

            raise ValueError(
                "Invalid MCP authentication timestamp."
            )

        if (
            age
            > TOKEN_TTL_SECONDS
        ):

            raise ValueError(
                "MCP authentication context expired."
            )

        user_id = payload.get(
            "user_id"
        )

        if not user_id:

            raise ValueError(
                "MCP authentication context "
                "does not contain a user ID."
            )

        return {

            "user_id":
                str(user_id),

            "issued_at":
                issued_at,
        }

    except ValueError:

        raise

    except Exception as error:

        raise ValueError(
            "Invalid MCP authentication context."
        ) from error