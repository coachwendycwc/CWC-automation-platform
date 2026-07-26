"""Invite-only registration: user_invites table

Registration is now gated behind single-use, expiring invites created by an
admin. The invite carries the role the new user will get; /auth/register
consumes it. First-admin bootstrap stays on scripts/seed_dev_user.py (direct
DB insert), so gating registration cannot lock everyone out.

Revision ID: 013
Revises: 012
Create Date: 2026-07-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_invites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("invited_by", sa.String(36), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True
        ),
    )
    op.create_index("ix_user_invites_email", "user_invites", ["email"])
    op.create_index("ix_user_invites_token", "user_invites", ["token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_invites_token", table_name="user_invites")
    op.drop_index("ix_user_invites_email", table_name="user_invites")
    op.drop_table("user_invites")
