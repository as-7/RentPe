"""merge branches

Revision ID: b67496eca362
Revises: 2ebfc70fc0fc, d7a4e2b7c9f1
Create Date: 2026-03-23 21:13:42.514187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b67496eca362'
down_revision: Union[str, Sequence[str], None] = ('2ebfc70fc0fc', 'd7a4e2b7c9f1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
