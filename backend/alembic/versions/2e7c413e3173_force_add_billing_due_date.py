"""force_add_billing_due_date

Revision ID: 2e7c413e3173
Revises: b67496eca362
Create Date: 2026-03-23 21:17:11.185355

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e7c413e3173'
down_revision: Union[str, Sequence[str], None] = 'b67496eca362'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS billing_due_date INTEGER NOT NULL DEFAULT 1;")


def downgrade() -> None:
    """Downgrade schema."""
    pass
