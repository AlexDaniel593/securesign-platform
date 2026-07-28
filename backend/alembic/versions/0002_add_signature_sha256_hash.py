"""add sha256_hash to signatures

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-27

Adds a denormalized ``sha256_hash`` column to the ``signatures`` table so that
queries can find signatures by content hash rather than only by document_id.
Migration: add nullable column → backfill from documents → NOT NULL → index.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add nullable column
    op.add_column(
        "signatures",
        sa.Column("sha256_hash", sa.String(64), nullable=True),
    )

    # 2. Backfill from documents table
    op.execute(
        """
        UPDATE signatures SET sha256_hash = (
            SELECT documents.sha256_hash FROM documents
            WHERE documents.id = signatures.document_id
        )
        """
    )

    # 3. NOT NULL constraint
    op.alter_column("signatures", "sha256_hash", nullable=False)

    # 4. Index for sha256_hash-based queries
    op.create_index(
        "idx_signatures_sha256_hash", "signatures", ["sha256_hash"]
    )


def downgrade() -> None:
    op.drop_index("idx_signatures_sha256_hash", table_name="signatures")
    op.drop_column("signatures", "sha256_hash")
