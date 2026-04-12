"""Add calendar connections for multi-calendar support

Revision ID: 011_calendar_connections
Revises: c5e8f12a3b4d
Create Date: 2026-04-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "011_calendar_connections"
down_revision: Union[str, None] = "c5e8f12a3b4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("account_email", sa.String(255), nullable=True),
        sa.Column("account_name", sa.String(255), nullable=True),
        sa.Column("external_account_id", sa.String(255), nullable=True),
        sa.Column("calendar_id", sa.String(255), nullable=False, server_default="primary"),
        sa.Column("calendar_name", sa.String(255), nullable=True),
        sa.Column("token_data", sa.JSON(), nullable=True),
        sa.Column("sync_direction", sa.String(20), nullable=False, server_default="read_write"),
        sa.Column("conflict_check_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("provider_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index("ix_calendar_connections_user_id", "calendar_connections", ["user_id"])
    op.create_index("ix_calendar_connections_provider", "calendar_connections", ["provider"])
    op.create_index("ix_calendar_connections_account_email", "calendar_connections", ["account_email"])
    op.create_index("ix_calendar_connections_external_account_id", "calendar_connections", ["external_account_id"])


def downgrade() -> None:
    op.drop_index("ix_calendar_connections_external_account_id", table_name="calendar_connections")
    op.drop_index("ix_calendar_connections_account_email", table_name="calendar_connections")
    op.drop_index("ix_calendar_connections_provider", table_name="calendar_connections")
    op.drop_index("ix_calendar_connections_user_id", table_name="calendar_connections")
    op.drop_table("calendar_connections")
