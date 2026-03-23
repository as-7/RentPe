"""add reminder logs table

Revision ID: d7a4e2b7c9f1
Revises: c1f4d9a7b8e2
Create Date: 2026-03-10 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7a4e2b7c9f1'
down_revision: Union[str, Sequence[str], None] = 'c1f4d9a7b8e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'reminder_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('target_due_date', sa.Date(), nullable=False),
        sa.Column('days_before_due', sa.Integer(), nullable=False),
        sa.Column('tenant_mobile', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('provider_message_id', sa.String(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reminder_logs_id'), 'reminder_logs', ['id'], unique=False)
    op.create_index(op.f('ix_reminder_logs_property_id'), 'reminder_logs', ['property_id'], unique=False)
    op.create_index(op.f('ix_reminder_logs_room_id'), 'reminder_logs', ['room_id'], unique=False)
    op.create_index(op.f('ix_reminder_logs_target_due_date'), 'reminder_logs', ['target_due_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_reminder_logs_target_due_date'), table_name='reminder_logs')
    op.drop_index(op.f('ix_reminder_logs_room_id'), table_name='reminder_logs')
    op.drop_index(op.f('ix_reminder_logs_property_id'), table_name='reminder_logs')
    op.drop_index(op.f('ix_reminder_logs_id'), table_name='reminder_logs')
    op.drop_table('reminder_logs')
