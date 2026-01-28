"""Add password auth fields to users

Revision ID: 006
Revises: 005
Create Date: 2024-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password auth fields to users table
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('users', sa.Column('password_reset_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_reset_expires')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'password_hash')
