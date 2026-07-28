"""rename file_path to object_key

Revision ID: 0001
Revises:
Create Date: 2026-07-23

The rename is guarded by an existence check so the migration is safe on
both existing DBs (which have ``file_path``) and fresh DBs created by
``SQLModel.metadata.create_all()`` (which already have ``object_key``).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("documents")]

    if "file_path" in columns:
        # Works on SQLite >= 3.25 and PostgreSQL >= 9
        op.execute("ALTER TABLE documents RENAME COLUMN file_path TO object_key")


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("documents")]

    if "object_key" in columns and "file_path" not in columns:
        op.execute("ALTER TABLE documents RENAME COLUMN object_key TO file_path")
