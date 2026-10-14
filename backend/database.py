
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPOSITORY_ROOT / ".env")

database_url = make_url(
    os.getenv("DATABASE_URL", "sqlite:///./students.db")
)

if (
    database_url.get_backend_name() == "sqlite"
    and database_url.database
    and not Path(database_url.database).is_absolute()
):
    database_url = database_url.set(
        database=str(
            (REPOSITORY_ROOT / database_url.database).resolve()
        )
    )

DATABASE_URL = database_url.render_as_string(hide_password=False)

connect_args = (
    {"check_same_thread": False}
    if database_url.get_backend_name() == "sqlite"
    else {}
)

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
