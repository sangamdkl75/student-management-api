from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Integer, String, create_engine, inspect, text

from database import DATABASE_URL


PROJECT_ROOT = Path(__file__).resolve().parent
BASELINE_REVISION = "f16e6f5db93c"
ROLE_REVISION = "f8fdb94d842b"
HEAD_REVISION = "27e3a8b8ec85"

USER_COLUMNS = {"id", "username", "password_hash"}
STUDENT_COLUMNS = {"id", "name", "age", "course"}
APPLICATION_TABLES = {"users", "students"}
KNOWN_REVISIONS = {BASELINE_REVISION, ROLE_REVISION, HEAD_REVISION}
EXPECTED_TYPES = {
    "users": {
        "id": Integer,
        "username": String,
        "password_hash": String,
        "role": String,
    },
    "students": {
        "id": Integer,
        "name": String,
        "age": Integer,
        "course": String,
        "user_id": Integer,
    },
}


def _config_for_database(database_url: str) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.attributes["database_url"] = database_url
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def _inspect_application_schema(connection) -> tuple[bool, bool, bool]:
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    present_tables = tables.intersection(APPLICATION_TABLES)

    if not present_tables:
        if tables:
            raise RuntimeError(
                "Cannot initialize database: found tables unrelated to this application"
            )
        return False, False, False
    if present_tables != APPLICATION_TABLES:
        raise RuntimeError(
            "Cannot adopt database: only one of users and students exists"
        )
    unexpected_tables = tables - APPLICATION_TABLES - {"alembic_version"}
    if unexpected_tables:
        raise RuntimeError(
            "Cannot adopt database: found tables unrelated to this application"
        )

    user_column_info = {
        column["name"]: column for column in inspector.get_columns("users")
    }
    student_column_info = {
        column["name"]: column for column in inspector.get_columns("students")
    }
    user_columns = set(user_column_info)
    student_columns = set(student_column_info)
    if (
        not USER_COLUMNS.issubset(user_columns)
        or not user_columns.issubset(USER_COLUMNS | {"role"})
        or not STUDENT_COLUMNS.issubset(student_columns)
        or not student_columns.issubset(STUDENT_COLUMNS | {"user_id"})
    ):
        raise RuntimeError(
            "Cannot adopt database: users or students has an unknown schema"
        )

    for table_name, column_info in (
        ("users", user_column_info),
        ("students", student_column_info),
    ):
        primary_key = inspector.get_pk_constraint(table_name).get(
            "constrained_columns"
        )
        if primary_key != ["id"]:
            raise RuntimeError(
                f"Cannot adopt database: {table_name}.id is not its primary key"
            )
        for column_name, column in column_info.items():
            expected_type = EXPECTED_TYPES[table_name][column_name]
            if not isinstance(column["type"], expected_type):
                raise RuntimeError(
                    f"Cannot adopt database: unexpected type for "
                    f"{table_name}.{column_name}"
                )

    unique_usernames = any(
        constraint.get("column_names") == ["username"]
        for constraint in inspector.get_unique_constraints("users")
    )
    if not unique_usernames:
        unique_usernames = any(
            index.get("column_names") == ["username"] and index.get("unique")
            for index in inspector.get_indexes("users")
        )
    if not unique_usernames:
        raise RuntimeError(
            "Cannot adopt database: users.username is not unique"
        )

    if "role" in user_column_info and user_column_info["role"]["nullable"] is False:
        raise RuntimeError("Cannot adopt database: users.role must be nullable")
    if (
        "user_id" in student_column_info
        and student_column_info["user_id"]["nullable"] is False
    ):
        raise RuntimeError(
            "Cannot adopt database: students.user_id must be nullable"
        )

    all_foreign_keys = inspector.get_foreign_keys("students")
    unexpected_foreign_keys = [
        foreign_key
        for foreign_key in all_foreign_keys
        if foreign_key.get("constrained_columns") != ["user_id"]
    ]
    user_id_foreign_keys = [
        foreign_key
        for foreign_key in all_foreign_keys
        if foreign_key.get("constrained_columns") == ["user_id"]
    ]
    if unexpected_foreign_keys or any(
        foreign_key.get("referred_table") != "users"
        or foreign_key.get("referred_columns") != ["id"]
        for foreign_key in user_id_foreign_keys
    ):
        raise RuntimeError(
            "Cannot adopt database: students.user_id has an unexpected foreign key"
        )

    has_role = "role" in user_columns
    has_user_id = "user_id" in student_columns
    if has_user_id and connection.execute(
        text(
            "SELECT 1 FROM students AS s "
            "LEFT JOIN users AS u ON u.id = s.user_id "
            "WHERE s.user_id IS NOT NULL AND u.id IS NULL LIMIT 1"
        )
    ).first():
        raise RuntimeError(
            "Cannot adopt database: students.user_id contains unknown users"
        )

    if user_id_foreign_keys and not has_user_id:
        raise RuntimeError(
            "Cannot adopt database: students has an ownership foreign key "
            "without its column"
        )
    if len(user_id_foreign_keys) > 1:
        raise RuntimeError(
            "Cannot adopt database: multiple student ownership foreign keys exist"
        )

    return has_role, has_user_id, bool(user_id_foreign_keys)


def _revision_for_unversioned_schema(connection) -> str | None:
    has_role, has_user_id, has_user_id_foreign_key = (
        _inspect_application_schema(connection)
    )
    if not inspect(connection).get_table_names():
        return None

    if not has_role and not has_user_id:
        return BASELINE_REVISION
    if has_role and not has_user_id:
        return ROLE_REVISION
    if has_role and has_user_id and has_user_id_foreign_key:
        return HEAD_REVISION
    raise RuntimeError(
        "Cannot adopt database: schema does not match a supported application revision"
    )


def _validate_version_table(connection) -> str:
    inspector = inspect(connection)
    columns = inspector.get_columns("alembic_version")
    primary_key = inspector.get_pk_constraint("alembic_version").get(
        "constrained_columns"
    )
    if (
        len(columns) != 1
        or columns[0]["name"] != "version_num"
        or not isinstance(columns[0]["type"], String)
        or primary_key != ["version_num"]
    ):
        raise RuntimeError(
            "Cannot upgrade database: malformed Alembic version table"
        )

    revisions = connection.exec_driver_sql(
        "SELECT version_num FROM alembic_version"
    ).scalars().all()
    if len(revisions) != 1:
        raise RuntimeError(
            "Cannot upgrade database: expected exactly one Alembic revision"
        )
    revision = revisions[0]
    if revision not in KNOWN_REVISIONS:
        raise RuntimeError(
            "Cannot upgrade database: unrecognized Alembic revision"
        )
    return revision


def _validate_recorded_schema(connection, revision: str) -> None:
    has_role, has_user_id, has_user_id_foreign_key = (
        _inspect_application_schema(connection)
    )
    if revision == BASELINE_REVISION and (has_role or has_user_id):
        raise RuntimeError(
            "Cannot upgrade database: schema does not match its baseline revision"
        )
    if revision == ROLE_REVISION and not has_role:
        raise RuntimeError(
            "Cannot upgrade database: users.role is missing for its recorded revision"
        )
    if revision == HEAD_REVISION and not (
        has_role and has_user_id and has_user_id_foreign_key
    ):
        raise RuntimeError(
            "Cannot upgrade database: schema does not match the recorded head revision"
        )


def initialize_database(database_url: str = DATABASE_URL) -> None:
    """Safely adopt a known legacy schema, then upgrade it to Alembic head."""
    config = _config_for_database(database_url)

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            tables = set(inspect(connection).get_table_names())
            if "alembic_version" not in tables:
                revision = _revision_for_unversioned_schema(connection)
            else:
                revision = _validate_version_table(connection)
                _validate_recorded_schema(connection, revision)
            if "alembic_version" in tables and not (
                tables.intersection(APPLICATION_TABLES) == APPLICATION_TABLES
            ):
                raise RuntimeError(
                    "Cannot upgrade database: Alembic version exists without "
                    "both application tables"
                )
        if revision is not None and "alembic_version" not in tables:
            command.stamp(config, revision)
    finally:
        engine.dispose()

    command.upgrade(config, "head")


if __name__ == "__main__":
    initialize_database()
