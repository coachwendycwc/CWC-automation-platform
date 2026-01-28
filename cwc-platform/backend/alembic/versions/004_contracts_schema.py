"""Contracts & E-Signatures schema - Phase 4

Revision ID: 004
Revises: 003
Create Date: 2025-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Contract templates table
    op.create_table(
        "contract_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("content", sa.Text, nullable=False),  # HTML with merge fields
        sa.Column("category", sa.String(50), nullable=False, server_default="coaching"),
        sa.Column("merge_fields", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("default_expiry_days", sa.Integer, nullable=False, server_default="7"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Contracts table
    op.create_table(
        "contracts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contract_number", sa.String(20), unique=True, nullable=False),
        # Source template
        sa.Column(
            "template_id",
            sa.String(36),
            sa.ForeignKey("contract_templates.id", ondelete="SET NULL"),
            index=True,
        ),
        # Client info
        sa.Column(
            "contact_id",
            sa.String(36),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "organization_id",
            sa.String(36),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            index=True,
        ),
        # Content
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text, nullable=False),  # Rendered HTML
        # Status tracking
        sa.Column("status", sa.String(20), nullable=False, server_default="draft", index=True),
        sa.Column("sent_at", sa.DateTime),
        sa.Column("viewed_at", sa.DateTime),
        sa.Column("signed_at", sa.DateTime),
        sa.Column("expires_at", sa.DateTime),
        sa.Column("declined_at", sa.DateTime),
        sa.Column("decline_reason", sa.Text),
        # Signature data
        sa.Column("signer_name", sa.String(200)),
        sa.Column("signer_email", sa.String(255)),
        sa.Column("signer_ip", sa.String(45)),
        sa.Column("signature_data", sa.Text),  # Base64 encoded signature
        sa.Column("signature_type", sa.String(20)),  # "drawn" or "typed"
        # Audit hashes for legal validity
        sa.Column("content_hash", sa.String(64)),
        sa.Column("signature_hash", sa.String(64)),
        # Links to other entities
        sa.Column(
            "linked_invoice_id",
            sa.String(36),
            sa.ForeignKey("invoices.id", ondelete="SET NULL"),
        ),
        sa.Column("linked_project_id", sa.String(36)),  # Future use
        # Public access token
        sa.Column("view_token", sa.String(64), unique=True, nullable=False),
        # Notes
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Signature audit logs table
    op.create_table(
        "signature_audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "contract_id",
            sa.String(36),
            sa.ForeignKey("contracts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("action", sa.String(30), nullable=False),  # created, sent, viewed, signed, declined, expired, voided
        sa.Column("actor_email", sa.String(255)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text),
        sa.Column("details", sa.JSON),  # Additional context
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("signature_audit_logs")
    op.drop_table("contracts")
    op.drop_table("contract_templates")
