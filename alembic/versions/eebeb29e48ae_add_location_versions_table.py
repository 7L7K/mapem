"""add location_versions table

Revision ID: eebeb29e48ae
Revises: 8ebbf910f390
Create Date: 2025-06-14 01:28:00.369695

"""
from typing import Sequence, Union
from sqlalchemy.dialects.postgresql import UUID

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eebeb29e48ae'
down_revision: Union[str, None] = '8ebbf910f390'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'location_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=False),
        sa.Column('lat', sa.Float, nullable=False),
        sa.Column('lng', sa.Float, nullable=False),
        sa.Column('valid_from', sa.Integer),
        sa.Column('valid_to', sa.Integer),
        sa.Column('modern_equivalent', sa.String),
        sa.Column('source', sa.String),
        sa.Column('notes', sa.JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

def downgrade():
    op.drop_table('location_versions')
