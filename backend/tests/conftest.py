import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite://"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import Base, engine as application_engine
from main import app
from routers import auth as auth_router
from routers import students as students_router


@pytest.fixture
def client():
    if application_engine.url.database is not None:
        raise RuntimeError("Tests must not use a file-backed application database")

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[auth_router.get_db] = override_get_db
    app.dependency_overrides[students_router.get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client, testing_session_local
    finally:
        app.dependency_overrides.pop(auth_router.get_db, None)
        app.dependency_overrides.pop(students_router.get_db, None)
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()