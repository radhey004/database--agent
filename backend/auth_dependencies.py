from fastapi import (
    Cookie,
    HTTPException,
)

from .auth import (
    AuthenticationError,
    decode_access_token,
    get_user_by_id,
)

from .config import (
    AUTH_COOKIE_NAME,
)


def get_current_user(
    dbagent_session: str | None = Cookie(
        default=None,
        alias=AUTH_COOKIE_NAME,
    ),
):

    if not dbagent_session:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated.",
        )

    try:

        user_id = decode_access_token(
            dbagent_session
        )

    except AuthenticationError as error:

        raise HTTPException(
            status_code=401,
            detail=str(error),
        )

    user = get_user_by_id(
        user_id
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="User account not found.",
        )

    return user