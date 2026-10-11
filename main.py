import os
from urllib.parse import urlsplit

from fastapi import FastAPI

from routers.students import router as student_router
from routers.auth import router as auth_router

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Student Management API"
)


def get_allowed_origins(frontend_origin: str | None = None) -> list[str]:
    origins = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ]

    if frontend_origin is None or not frontend_origin.strip():
        return origins

    origin = frontend_origin.strip()
    parsed_origin = urlsplit(origin)
    if (
        "*" in origin
        or parsed_origin.scheme not in {"http", "https"}
        or not parsed_origin.netloc
        or parsed_origin.path not in {"", "/"}
        or parsed_origin.query
        or parsed_origin.fragment
        or parsed_origin.username
        or parsed_origin.password
    ):
        raise ValueError(
            "FRONTEND_ORIGIN must be a single explicit HTTP(S) origin"
        )

    origins.append(origin.rstrip("/"))
    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(os.getenv("FRONTEND_ORIGIN")),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Student Management API"
    }


app.include_router(student_router)
app.include_router(auth_router)