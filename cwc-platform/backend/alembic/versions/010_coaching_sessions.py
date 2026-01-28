"""Add coaching sessions table for ICF tracking

Revision ID: 010
Revises: 009
Create Date: 2026-01-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'coaching_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contact_id', sa.String(36), sa.ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True, index=True),

        # Client info (for sessions without linked contact)
        sa.Column('client_name', sa.String(255), nullable=False),
        sa.Column('client_email', sa.String(255), nullable=True),

        # Session details
        sa.Column('session_date', sa.Date(), nullable=False, index=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_hours', sa.Float(), nullable=False, default=1.0),

        # ICF classification
        sa.Column('session_type', sa.String(20), nullable=False, default='individual', index=True),
        sa.Column('group_size', sa.Integer(), nullable=True),

        # Payment classification
        sa.Column('payment_type', sa.String(20), nullable=False, default='paid', index=True),

        # Source tracking
        sa.Column('source', sa.String(50), nullable=False, default='manual', index=True),
        sa.Column('external_id', sa.String(255), nullable=True),

        # Meeting details
        sa.Column('meeting_title', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        # Status
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Additional indexes
    op.create_index('ix_coaching_sessions_client_name', 'coaching_sessions', ['client_name'])


def downgrade() -> None:
    op.drop_index('ix_coaching_sessions_client_name', 'coaching_sessions')
    op.drop_table('coaching_sessions')
