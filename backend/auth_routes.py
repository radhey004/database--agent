import re

from fastapi import (
    APIRouter,
    Cookie,
    HTTPException,
    Response,
)

from pydantic import (
    BaseModel,
    EmailStr,
)

from .auth import (
    AuthenticationError,
    authenticate_user,
    create_access_token,
    create_user,
    decode_access_token,
    get_user_by_id,
    init_auth_database,
)

from .config import (
    AUTH_COOKIE_NAME,
    AUTH_COOKIE_SECURE,
    JWT_EXPIRE_DAYS,
    TERMS_VERSION,
)
from .approval_store import (
    init_approval_store,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class RegisterRequest(
    BaseModel
):

    email: EmailStr

    password: str

    accept_terms: bool


class LoginRequest(
    BaseModel
):

    email: EmailStr

    password: str


# ============================================================
# PASSWORD VALIDATION
# ============================================================

def validate_password(
    password: str,
):

    if len(password) < 8:

        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain "
                "at least 8 characters."
            ),
        )

    if not re.search(
        r"[A-Za-z]",
        password,
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain "
                "at least one letter."
            ),
        )

    if not re.search(
        r"\d",
        password,
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain "
                "at least one number."
            ),
        )


# ============================================================
# COOKIE
# ============================================================

def set_auth_cookie(
    response: Response,
    token: str,
):

    response.set_cookie(

        key=AUTH_COOKIE_NAME,

        value=token,

        max_age=(
            JWT_EXPIRE_DAYS
            * 24
            * 60
            * 60
        ),

        httponly=True,

        secure=AUTH_COOKIE_SECURE,

        samesite="none",

        path="/",
    )


def clear_auth_cookie(
    response: Response,
):

    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
    )


# ============================================================
# STARTUP
# ============================================================

@router.on_event(
    "startup"
)
async def initialize_auth():

    init_auth_database()
    init_approval_store()


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register"
)
async def register(
    data: RegisterRequest,
    response: Response,
):

    if not data.accept_terms:

        raise HTTPException(
            status_code=400,
            detail=(
                "You must accept the "
                "Terms & Conditions."
            ),
        )


    validate_password(
        data.password
    )


    try:

        user = create_user(

            email=data.email,

            password=data.password,
        )

    except AuthenticationError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


    token = create_access_token(
        user["id"]
    )

    set_auth_cookie(
        response,
        token,
    )


    return {

        "success": True,

        "message":
            "Account created successfully.",

        "user": user,

        "terms_version":
            TERMS_VERSION,
    }


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login"
)
async def login(
    data: LoginRequest,
    response: Response,
):

    try:

        user = authenticate_user(

            email=data.email,

            password=data.password,
        )

    except AuthenticationError as error:

        raise HTTPException(
            status_code=401,
            detail=str(error),
        )


    token = create_access_token(
        user["id"]
    )

    set_auth_cookie(
        response,
        token,
    )


    return {

        "success": True,

        "message":
            "Login successful.",

        "user": {

            "id":
                user["id"],

            "email":
                user["email"],

            "terms_version":
                user[
                    "terms_version"
                ],
        },
    }


# ============================================================
# CURRENT USER
# ============================================================

@router.get(
    "/me"
)
async def me(
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

        user = get_user_by_id(
            user_id
        )

    except AuthenticationError as error:

        raise HTTPException(
            status_code=401,
            detail=str(error),
        )


    if not user:

        raise HTTPException(
            status_code=401,
            detail="User account not found.",
        )


    return {

        "authenticated": True,

        "user": user,
    }


# ============================================================
# LOGOUT
# ============================================================

@router.post(
    "/logout"
)
async def logout(
    response: Response,
):

    clear_auth_cookie(
        response
    )

    return {

        "success": True,

        "message":
            "Logged out successfully.",
    }