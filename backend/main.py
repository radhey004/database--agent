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


app = FastAPI(
    title="DB Agent"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():

    return {
        "message": "DB Agent is running"
    }


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


@app.post("/ask")
async def ask(data: dict):

    question = data.get(
        "question",
        ""
    ).strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question is required"
        )

    try:

        return await ask_agent(
            question
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        print(
            "Agent error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Something went wrong "
                "while processing the request."
            )
        )


@app.post("/approve/{request_id}")
async def approve(request_id: str):

    try:

        return await approve_request(
            request_id
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        print(
            "Approval execution error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to execute "
                "approved modification."
            )
        )


@app.post("/reject/{request_id}")
async def reject(request_id: str):

    try:

        return reject_approval(
            request_id
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )