"""Add billing_due_date to properties

Revision ID: 2ebfc70fc0fc
Revises: 427f310b3c52
Create Date: 2026-03-06 11:44:41.723377

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ebfc70fc0fc'
down_revision: Union[str, Sequence[str], None] = '427f310b3c52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('properties', sa.Column('billing_due_date', sa.Integer(), server_default='1', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('properties', 'billing_due_date')
