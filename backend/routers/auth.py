import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import os

import models
import schemas
from database import SessionLocal


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_secret_key(secret_key: str | None) -> str:
    if secret_key is None or not secret_key.strip():
        raise RuntimeError("SECRET_KEY must be set")

    if len(secret_key.encode("utf-8")) < 32:
        raise RuntimeError("SECRET_KEY must contain at least 32 bytes")

    return secret_key


def get_access_token_expiry_minutes(value: str | None) -> int:
    if value is None:
        return 30
    try:
        minutes = int(value)
    except ValueError as error:
        raise RuntimeError(
            "ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer"
        ) from error
    if minutes <= 0:
        raise RuntimeError(
            "ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer"
        )
    return minutes


SECRET_KEY = get_secret_key(os.getenv("SECRET_KEY"))
ACCESS_TOKEN_EXPIRE_MINUTES = get_access_token_expiry_minutes(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(
    registration: schemas.UserRegistration,
    db: Session = Depends(get_db)
):
    username = registration.username
    password = registration.password

    existing_user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    hashed_password = password_hash.hash(password)

    new_user = models.User(
        username=username,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registers successfully",
        "username": new_user.username
    }

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    username = form_data.username
    password = form_data.password

    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not password_hash.verify(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    token_data = {
        "sub": user.username,
        "exp": expires_at,
    }

    token = jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm="HS256"
    )

   
    return{
        "access_token": token,
        "token_type": "bearer"
    }

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        username = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user

def get_current_admin(
        current_user = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user