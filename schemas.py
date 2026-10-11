from pydantic import BaseModel, Field


class UserRegistration(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class Student(BaseModel):
    name: str
    age: int
    course: str


class StudentUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    course: str | None = None