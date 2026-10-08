from pydantic import BaseModel


class Student(BaseModel):
    name: str
    age: int
    course: str


class StudentUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    course: str | None = None