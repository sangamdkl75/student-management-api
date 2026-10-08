from fastapi import FastAPI

from database import engine, Base
from routers.students import router as student_router
from routers.auth import router as auth_router
import models


app = FastAPI(
    title="Student Management API"
)


Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {
        "message": "Student Management API"
    }


app.include_router(student_router)
app.include_router(auth_router)