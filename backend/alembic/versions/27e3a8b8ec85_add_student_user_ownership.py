"""add student user ownership

Revision ID: 27e3a8b8ec85
Revises: f8fdb94d842b
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "27e3a8b8ec85"
down_revision: Union[str, Sequence[str], None] = (
    "f8fdb94d842b",
    "f16e6f5db93c",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("students")}

    if "user_id" not in columns:
        with op.batch_alter_table("students", recreate="always") as batch_op:
            batch_op.add_column(
                sa.Column("user_id", sa.Integer(), nullable=True)
            )

    foreign_keys = inspector.get_foreign_keys("students")
    matching_foreign_keys = [
        foreign_key
        for foreign_key in foreign_keys
        if foreign_key.get("constrained_columns") == ["user_id"]
        and foreign_key.get("referred_table") == "users"
        and foreign_key.get("referred_columns") == ["id"]
    ]

    if len(matching_foreign_keys) > 1:
        raise RuntimeError("Multiple student user ownership foreign keys exist")
    if matching_foreign_keys:
        return
    if any(foreign_key.get("constrained_columns") == ["user_id"] for foreign_key in foreign_keys):
        raise RuntimeError("students.user_id has an unexpected foreign key")

    with op.batch_alter_table("students", recreate="always") as batch_op:
        batch_op.create_foreign_key(
            "fk_students_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )


def downgrade() -> None:
    foreign_keys = sa.inspect(op.get_bind()).get_foreign_keys("students")
    if any(
        foreign_key.get("name") == "fk_students_user_id_users"
        for foreign_key in foreign_keys
    ):
        with op.batch_alter_table("students", recreate="always") as batch_op:
            batch_op.drop_constraint(
                "fk_students_user_id_users",
                type_="foreignkey",
            )