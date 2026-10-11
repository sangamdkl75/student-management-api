from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True,index=True)
    name = Column(String)
    age = Column(Integer)
    course = Column(String)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="user")