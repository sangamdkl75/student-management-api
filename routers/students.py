from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
import models
import schemas
from routers.auth import get_current_user, get_current_admin

router = APIRouter(
    prefix="/students",
    tags=["Students"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/")
def get_students(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    return db.query(models.Student).all()


@router.get("/{student_id}")
def get_student(
    student_id: int,
    db: Session = Depends(get_db)
):
    student = db.query(models.Student).filter(
        models.Student.id == student_id
    ).first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return student


@router.post("/", status_code=201)
def create_student(
    student: schemas.Student,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    new_student = models.Student(
        name=student.name,
        age=student.age,
        course=student.course
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student


@router.put("/{student_id}")
def update_student(
    student_id: int,
    student: schemas.Student,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)

):
    existing_student = db.query(models.Student).filter(
        models.Student.id == student_id
    ).first()

    if existing_student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    existing_student.name = student.name
    existing_student.age = student.age
    existing_student.course = student.course

    db.commit()
    db.refresh(existing_student)

    return existing_student


@router.patch("/{student_id}")
def patch_student(
    student_id: int,
    student: schemas.StudentUpdate,
    db: Session = Depends(get_db)
):
    existing_student = db.query(models.Student).filter(
        models.Student.id == student_id
    ).first()

    if existing_student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    if student.name is not None:
        existing_student.name = student.name

    if student.age is not None:
        existing_student.age = student.age

    if student.course is not None:
        existing_student.course = student.course

    db.commit()
    db.refresh(existing_student)

    return existing_student


@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    student = db.query(models.Student).filter(
        models.Student.id == student_id
    ).first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    db.delete(student)
    db.commit()

    return {
        "message": "Student deleted successfully"
    }

