"""add status & fixed_at

Revision ID: 8ebbf910f390
Revises: 650003afe3d6
Create Date: 2025-06-13 10:35:41.902306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ebbf910f390'
down_revision: Union[str, None] = '650003afe3d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema – add status & fixed_at to locations, safely."""
    conn = op.get_bind()

    # Add status column
    conn.execute(
        sa.text("ALTER TABLE locations ADD COLUMN IF NOT EXISTS status VARCHAR(32);")
    )

    # Add fixed_at column
    conn.execute(
        sa.text("ALTER TABLE locations ADD COLUMN IF NOT EXISTS fixed_at TIMESTAMP WITH TIME ZONE;")
    )

    # Create index if not exists (safely)
    result = conn.execute(sa.text("""
        SELECT indexname FROM pg_indexes WHERE tablename='locations' AND indexname='ix_locations_status'
    """)).fetchall()
    if not result:
        conn.execute(
            sa.text("CREATE INDEX ix_locations_status ON locations (status);")
        )

    # Optional backfill
    conn.execute(
        sa.text(
            """
            UPDATE locations
            SET status = 'ok'
            WHERE status IS NULL
              AND lat IS NOT NULL
              AND lng IS NOT NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE locations
            SET status = 'unresolved'
            WHERE status IS NULL
              AND (lat IS NULL OR lng IS NULL)
            """
        )
    )
