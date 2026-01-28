"""Initial schema - Phase 1

Revision ID: 001
Revises:
Create Date: 2025-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("google_id", sa.String(255), unique=True),
        sa.Column("avatar_url", sa.String(500)),
        sa.Column("role", sa.String(20), server_default="user"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(100)),
        sa.Column("size", sa.String(50)),
        sa.Column("website", sa.String(255)),
        sa.Column("primary_contact_id", sa.String(36)),
        sa.Column("billing_contact_id", sa.String(36)),
        sa.Column("tags", sa.JSON, server_default="[]"),
        sa.Column("segment", sa.String(50)),
        sa.Column("source", sa.String(100)),
        sa.Column("lifetime_value", sa.DECIMAL(12, 2), server_default="0"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Contacts table
    op.create_table(
        "contacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100)),
        sa.Column("email", sa.String(255), index=True),
        sa.Column("phone", sa.String(50)),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), index=True),
        sa.Column("role", sa.String(100)),
        sa.Column("title", sa.String(100)),
        sa.Column("contact_type", sa.String(20), server_default="lead", index=True),
        sa.Column("coaching_type", sa.String(20)),
        sa.Column("tags", sa.JSON, server_default="[]"),
        sa.Column("source", sa.String(100)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Interactions table
    op.create_table(
        "interactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contact_id", sa.String(36), sa.ForeignKey("contacts.id"), nullable=False, index=True),
        sa.Column("interaction_type", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(255)),
        sa.Column("content", sa.Text),
        sa.Column("direction", sa.String(10)),
        sa.Column("gmail_message_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id")),
    )

    # Fathom webhooks table
    op.create_table(
        "fathom_webhooks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recording_id", sa.String(100), unique=True),
        sa.Column("meeting_title", sa.String(255)),
        sa.Column("transcript", sa.Text),
        sa.Column("summary", sa.JSON),
        sa.Column("action_items", sa.JSON),
        sa.Column("attendees", sa.JSON),
        sa.Column("duration_seconds", sa.Integer),
        sa.Column("recorded_at", sa.DateTime),
        sa.Column("processed_at", sa.DateTime),
        sa.Column("processing_status", sa.String(20), server_default="pending", index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("fathom_webhooks")
    op.drop_table("interactions")
    op.drop_table("contacts")
    op.drop_table("organizations")
    op.drop_table("users")
