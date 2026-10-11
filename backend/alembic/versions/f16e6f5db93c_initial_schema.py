"""create the original users and students tables

Revision ID: f16e6f5db93c
Revises:
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f16e6f5db93c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_tables = set(sa.inspect(bind).get_table_names())

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("username", sa.String(), nullable=True),
            sa.Column("password_hash", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("username"),
        )
        op.create_index("ix_users_id", "users", ["id"], unique=False)
        op.create_index(
            "ix_users_username",
            "users",
            ["username"],
            unique=False,
        )

    if "students" not in existing_tables:
        op.create_table(
            "students",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("age", sa.Integer(), nullable=True),
            sa.Column("course", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_students_id", "students", ["id"], unique=False)


def downgrade() -> None:
    # This revision can adopt existing application tables, so ownership is unknown.
    pass
