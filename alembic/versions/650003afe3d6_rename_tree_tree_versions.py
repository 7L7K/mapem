"""rename tree → tree_versions

Revision ID: 650003afe3d6
Revises: 0e5caa1cc23d
Create Date: 2025-06-09 16:47:29.079752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '650003afe3d6'
down_revision: Union[str, None] = '0e5caa1cc23d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.rename_table('tree', 'tree_versions')

def downgrade():
    op.rename_table('tree_versions', 'tree')

