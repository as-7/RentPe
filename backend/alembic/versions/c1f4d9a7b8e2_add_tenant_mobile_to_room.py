"""add tenant_mobile to room

Revision ID: c1f4d9a7b8e2
Revises: a41fa3e9c148
Create Date: 2026-03-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1f4d9a7b8e2'
down_revision: Union[str, Sequence[str], None] = 'a41fa3e9c148'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('rooms', sa.Column('tenant_mobile', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('rooms', 'tenant_mobile')
