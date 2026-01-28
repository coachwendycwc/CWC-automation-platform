"""Invoicing schema - Phase 3

Revision ID: 003
Revises: 002
Create Date: 2025-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Invoices table
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("invoice_number", sa.String(20), unique=True, nullable=False),
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
        # Line items stored as JSON
        sa.Column("line_items", sa.JSON, nullable=False, server_default="[]"),
        # Totals
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("tax_rate", sa.Numeric(5, 2)),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("balance_due", sa.Numeric(12, 2), nullable=False, server_default="0"),
        # Payment terms
        sa.Column("payment_terms", sa.String(20), nullable=False, server_default="net_30"),
        sa.Column("due_date", sa.Date, nullable=False),
        # Status tracking
        sa.Column("status", sa.String(20), nullable=False, server_default="draft", index=True),
        sa.Column("sent_at", sa.DateTime),
        sa.Column("viewed_at", sa.DateTime),
        sa.Column("paid_at", sa.DateTime),
        # Payment plan support
        sa.Column("is_payment_plan", sa.Boolean, nullable=False, server_default="0"),
        # Token for public access
        sa.Column("view_token", sa.String(64), unique=True, nullable=False),
        # Notes
        sa.Column("notes", sa.Text),  # Internal notes
        sa.Column("memo", sa.Text),  # Appears on invoice
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Payments table
    op.create_table(
        "payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "invoice_id",
            sa.String(36),
            sa.ForeignKey("invoices.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_method", sa.String(20), nullable=False, server_default="other"),
        sa.Column("payment_date", sa.Date, nullable=False),
        # Stripe fields (for future)
        sa.Column("stripe_payment_intent_id", sa.String(100)),
        sa.Column("stripe_charge_id", sa.String(100)),
        # Reference info
        sa.Column("reference", sa.String(100)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(36)),
    )

    # Payment plans table
    op.create_table(
        "payment_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "invoice_id",
            sa.String(36),
            sa.ForeignKey("invoices.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("number_of_payments", sa.Integer, nullable=False),
        sa.Column("payment_frequency", sa.String(20), nullable=False, server_default="monthly"),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("schedule", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Fathom extractions table (AI extraction foundation)
    op.create_table(
        "fathom_extractions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "fathom_webhook_id",
            sa.String(36),
            sa.ForeignKey("fathom_webhooks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "contact_id",
            sa.String(36),
            sa.ForeignKey("contacts.id", ondelete="SET NULL"),
            index=True,
        ),
        sa.Column("extracted_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("confidence_scores", sa.JSON, nullable=False, server_default="{}"),
        sa.Column(
            "draft_invoice_id",
            sa.String(36),
            sa.ForeignKey("invoices.id", ondelete="SET NULL"),
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("reviewed_at", sa.DateTime),
        sa.Column("reviewed_by", sa.String(36)),
        sa.Column("corrections", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("review_notes", sa.String(500)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("fathom_extractions")
    op.drop_table("payment_plans")
    op.drop_table("payments")
    op.drop_table("invoices")
