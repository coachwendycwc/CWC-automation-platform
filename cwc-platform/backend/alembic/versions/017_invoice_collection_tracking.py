"""add invoice collection tracking

Revision ID: 017_invoice_collection_tracking
Revises: 016_booking_meeting_fields
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa


revision = "017_invoice_collection_tracking"
down_revision = "016_booking_meeting_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.add_column(sa.Column("due_soon_reminder_sent_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("overdue_reminder_sent_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("final_notice_sent_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("last_collection_email_sent_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.drop_column("last_collection_email_sent_at")
        batch_op.drop_column("final_notice_sent_at")
        batch_op.drop_column("overdue_reminder_sent_at")
        batch_op.drop_column("due_soon_reminder_sent_at")
