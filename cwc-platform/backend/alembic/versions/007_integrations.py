"""Add integration tokens to users

Revision ID: 007
Revises: 006
Create Date: 2024-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add integration token columns to users table
    op.add_column('users', sa.Column('google_calendar_token', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('zoom_token', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'zoom_token')
    op.drop_column('users', 'google_calendar_token')
