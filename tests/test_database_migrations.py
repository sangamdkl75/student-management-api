from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    inspect,
    text,
)
import pytest

import models
from database import Base
from initialize_database import initialize_database


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_REVISION = "f16e6f5db93c"
ROLE_REVISION = "f8fdb94d842b"
OWNERSHIP_REVISION = "27e3a8b8ec85"


def _database_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path.as_posix()}/migration-test.sqlite"


def _alembic_config(database_url: str) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.attributes["database_url"] = database_url
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def _create_original_schema(database_url: str, *, include_role: bool = False) -> None:
    metadata = MetaData()
    user_columns = [
        Column("id", Integer, primary_key=True),
        Column("username", String, unique=True),
        Column("password_hash", String),
    ]
    if include_role:
        user_columns.append(Column("role", String))
    Table("users", metadata, *user_columns)
    Table(
        "students",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String),
        Column("age", Integer),
        Column("course", String),
    )
    engine = create_engine(database_url)
    try:
        metadata.create_all(engine)
    finally:
        engine.dispose()


def _version(database_url: str) -> str:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            return connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
    finally:
        engine.dispose()


def test_fresh_database_initializes_to_head(tmp_path):
    database_url = _database_url(tmp_path)

    initialize_database(database_url)

    inspector_engine = create_engine(database_url)
    try:
        inspector = inspect(inspector_engine)
        assert {"users", "students", "alembic_version"}.issubset(
            inspector.get_table_names()
        )
        assert "role" in {
            column["name"] for column in inspector.get_columns("users")
        }
        assert "user_id" in {
            column["name"] for column in inspector.get_columns("students")
        }
        assert any(
            foreign_key.get("constrained_columns") == ["user_id"]
            and foreign_key.get("referred_table") == "users"
            and foreign_key.get("referred_columns") == ["id"]
            for foreign_key in inspector.get_foreign_keys("students")
        )
    finally:
        inspector_engine.dispose()

    assert _version(database_url) == OWNERSHIP_REVISION


def test_unversioned_legacy_data_is_adopted_and_preserved(tmp_path):
    database_url = _database_url(tmp_path)
    _create_original_schema(database_url)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO users (id, username, password_hash) "
                    "VALUES (1, 'legacy-user', 'test-hash')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO students (id, name, age, course) "
                    "VALUES (1, 'Legacy Student', 17, 'Math')"
                )
            )
    finally:
        engine.dispose()

    initialize_database(database_url)

    verify_engine = create_engine(database_url)
    try:
        with verify_engine.connect() as connection:
            assert connection.execute(
                text(
                    "SELECT username, password_hash, role "
                    "FROM users WHERE id = 1"
                )
            ).one() == ("legacy-user", "test-hash", None)
            assert connection.execute(
                text(
                    "SELECT name, age, course, user_id "
                    "FROM students WHERE id = 1"
                )
            ).one() == ("Legacy Student", 17, "Math", None)
    finally:
        verify_engine.dispose()

    assert _version(database_url) == OWNERSHIP_REVISION


def test_unversioned_schema_with_existing_role_is_adopted(tmp_path):
    database_url = _database_url(tmp_path)
    _create_original_schema(database_url, include_role=True)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO users "
                    "(id, username, password_hash, role) "
                    "VALUES (1, 'existing-role-user', 'test-hash', 'admin')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO students (id, name, age, course) "
                    "VALUES (1, 'Existing Role Student', 17, 'Math')"
                )
            )
    finally:
        engine.dispose()

    initialize_database(database_url)

    verify_engine = create_engine(database_url)
    try:
        with verify_engine.connect() as connection:
            assert connection.execute(
                text("SELECT username, role FROM users WHERE id = 1")
            ).one() == ("existing-role-user", "admin")
            assert connection.execute(
                text("SELECT name, user_id FROM students WHERE id = 1")
            ).one() == ("Existing Role Student", None)
    finally:
        verify_engine.dispose()

    assert _version(database_url) == OWNERSHIP_REVISION


def test_stamped_role_revision_upgrades_existing_data(tmp_path):
    database_url = _database_url(tmp_path)
    _create_original_schema(database_url, include_role=True)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO users "
                    "(id, username, password_hash, role) "
                    "VALUES (1, 'stamped-user', 'test-hash', 'admin')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO students (id, name, age, course) "
                    "VALUES (1, 'Stamped Student', 18, 'Science')"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE alembic_version "
                    "(version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO alembic_version (version_num) "
                    "VALUES (:revision)"
                ),
                {"revision": ROLE_REVISION},
            )
    finally:
        engine.dispose()

    initialize_database(database_url)

    verify_engine = create_engine(database_url)
    try:
        with verify_engine.connect() as connection:
            assert connection.execute(
                text("SELECT username, role FROM users WHERE id = 1")
            ).one() == ("stamped-user", "admin")
            assert connection.execute(
                text("SELECT name, user_id FROM students WHERE id = 1")
            ).one() == ("Stamped Student", None)
    finally:
        verify_engine.dispose()


def test_unrelated_tables_are_not_treated_as_fresh(tmp_path):
    database_url = _database_url(tmp_path)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE unrelated_data "
                    "(id INTEGER PRIMARY KEY, value TEXT NOT NULL)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO unrelated_data (id, value) "
                    "VALUES (1, 'preserve-me')"
                )
            )
    finally:
        engine.dispose()

    with pytest.raises(RuntimeError, match="unrelated to this application"):
        initialize_database(database_url)

    verify_engine = create_engine(database_url)
    try:
        with verify_engine.connect() as connection:
            assert inspect(connection).get_table_names() == ["unrelated_data"]
            assert connection.execute(
                text("SELECT value FROM unrelated_data WHERE id = 1")
            ).scalar_one() == "preserve-me"
    finally:
        verify_engine.dispose()


def test_alembic_version_without_application_tables_is_refused_unchanged(
    tmp_path,
):
    database_url = _database_url(tmp_path)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE alembic_version "
                    "(version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO alembic_version (version_num) "
                    "VALUES (:revision)"
                ),
                {"revision": OWNERSHIP_REVISION},
            )
    finally:
        engine.dispose()

    with pytest.raises(RuntimeError, match="unrelated to this application"):
        initialize_database(database_url)

    verify_engine = create_engine(database_url)
    try:
        with verify_engine.connect() as connection:
            assert inspect(connection).get_table_names() == ["alembic_version"]
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == OWNERSHIP_REVISION
    finally:
        verify_engine.dispose()


def test_stamped_head_with_incomplete_schema_is_refused_unchanged(tmp_path):
    database_url = _database_url(tmp_path)
    _create_original_schema(database_url)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE alembic_version "
                    "(version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO alembic_version (version_num) "
                    "VALUES (:revision)"
                ),
                {"revision": OWNERSHIP_REVISION},
            )
    finally:
        engine.dispose()

    with pytest.raises(RuntimeError, match="schema does not match"):
        initialize_database(database_url)

    verify_engine = create_engine(database_url)
    try:
        with verify_engine.connect() as connection:
            assert set(inspect(connection).get_table_names()) == {
                "users",
                "students",
                "alembic_version",
            }
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == OWNERSHIP_REVISION
            assert "role" not in {
                column["name"] for column in inspect(connection).get_columns("users")
            }
            assert "user_id" not in {
                column["name"]
                for column in inspect(connection).get_columns("students")
            }
    finally:
        verify_engine.dispose()

    assert _version(database_url) == OWNERSHIP_REVISION


def test_unrecognized_unversioned_schema_is_not_stamped_or_changed(tmp_path):
    database_url = _database_url(tmp_path)
    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("username", String),
        Column("password_hash", String),
    )
    Table(
        "students",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String),
        Column("age", Integer),
        Column("course", String),
    )
    engine = create_engine(database_url)
    try:
        metadata.create_all(engine)
    finally:
        engine.dispose()

    with pytest.raises(RuntimeError, match="users.username is not unique"):
        initialize_database(database_url)

    verify_engine = create_engine(database_url)
    try:
        assert "alembic_version" not in inspect(verify_engine).get_table_names()
    finally:
        verify_engine.dispose()


def test_current_schema_initialization_is_repeatable(tmp_path):
    database_url = _database_url(tmp_path)
    engine = create_engine(database_url)
    try:
        Base.metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO users "
                    "(id, username, password_hash, role) "
                    "VALUES (1, 'current-user', 'test-hash', 'user')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO students "
                    "(id, name, age, course, user_id) "
                    "VALUES (1, 'Current Student', 16, 'Art', 1)"
                )
            )
    finally:
        engine.dispose()

    initialize_database(database_url)
    initialize_database(database_url)

    verify_engine = create_engine(database_url)
    try:
        with verify_engine.connect() as connection:
            assert connection.execute(
                text("SELECT username, role FROM users WHERE id = 1")
            ).one() == ("current-user", "user")
            assert connection.execute(
                text("SELECT name, user_id FROM students WHERE id = 1")
            ).one() == ("Current Student", 1)
    finally:
        verify_engine.dispose()

    assert _version(database_url) == OWNERSHIP_REVISION


def test_ownership_downgrade_preserves_user_id_and_data(tmp_path):
    database_url = _database_url(tmp_path)
    initialize_database(database_url)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO users "
                    "(id, username, password_hash, role) "
                    "VALUES (1, 'owner', 'test-hash', 'user')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO students "
                    "(id, name, age, course, user_id) "
                    "VALUES (1, 'Owned Student', 19, 'History', 1)"
                )
            )
    finally:
        engine.dispose()

    command.downgrade(_alembic_config(database_url), ROLE_REVISION)

    inspector_engine = create_engine(database_url)
    try:
        inspector = inspect(inspector_engine)
        assert "user_id" in {
            column["name"] for column in inspector.get_columns("students")
        }
        assert not any(
            foreign_key.get("name") == "fk_students_user_id_users"
            for foreign_key in inspector.get_foreign_keys("students")
        )
        with inspector_engine.connect() as connection:
            assert connection.execute(
                text("SELECT name, user_id FROM students WHERE id = 1")
            ).one() == ("Owned Student", 1)
    finally:
        inspector_engine.dispose()


def test_migration_graph_preserves_published_root_and_has_one_head():
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    ownership = script.get_revision(OWNERSHIP_REVISION)

    assert script.get_heads() == [OWNERSHIP_REVISION]
    assert script.get_revision(BASELINE_REVISION).down_revision is None
    assert ownership.down_revision == (ROLE_REVISION, BASELINE_REVISION)
    assert models.Student.__table__.c.user_id.nullable is True
