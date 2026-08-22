from fastapi import (
    FastAPI,
    HTTPException,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from .agent import (
    ask_agent,
    approve_request,
    reject_approval,
)

from .database_routes import (
    router as database_router,
)


app = FastAPI(
    title="Database AI Agent V2",
    version="2.0.0",
)


app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


app.include_router(
    database_router
)


@app.get("/")
def home():

    return {

        "name":
            "Database AI Agent",

        "version":
            "2.0.0",

        "status":
            "running",
    }


@app.get("/health")
async def health():

    return {

        "status":
            "ok",
    }


@app.post("/ask")
async def ask(
    data: dict,
):

    question = data.get(
        "question",
        "",
    ).strip()


    connection_id = data.get(
        "connection_id",
        "",
    ).strip()


    if not question:

        raise HTTPException(

            status_code=400,

            detail=(
                "Question is required."
            ),
        )


    if not connection_id:

        raise HTTPException(

            status_code=400,

            detail=(
                "Database connection ID "
                "is required."
            ),
        )


    try:

        return await ask_agent(

            question,

            connection_id,
        )


    except ValueError as error:

        raise HTTPException(

            status_code=400,

            detail=str(error),
        )


    except Exception as error:

        print(
            "Agent error:",
            error,
        )

        raise HTTPException(

            status_code=500,

            detail=(
                "Something went wrong "
                "while processing the request."
            ),
        )


@app.post(
    "/approve/{request_id}"
)
async def approve(
    request_id: str,
):

    try:

        return await approve_request(
            request_id
        )


    except ValueError as error:

        raise HTTPException(

            status_code=400,

            detail=str(error),
        )


    except Exception as error:

        print(
            "Approval error:",
            error,
        )

        raise HTTPException(

            status_code=500,

            detail=(
                "Failed to execute "
                "approved modification."
            ),
        )


@app.post(
    "/reject/{request_id}"
)
async def reject(
    request_id: str,
):

    try:

        return reject_approval(
            request_id
        )


    except ValueError as error:

        raise HTTPException(

            status_code=400,

            detail=str(error),
        )


    except Exception as error:

        print(
            "Rejection error:",
            error,
        )

        raise HTTPException(

            status_code=500,

            detail=(
                "Failed to reject request."
            ),
        )