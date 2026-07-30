"""Capability tokens expire

Invoice pay-links and testimonial recording links are bearer credentials that
sit in an inbox forever. This bounds how long one works.

Existing rows are BACKFILLED rather than invalidated — an in-flight invoice
link that suddenly stopped working would be a support call, not a security
win. Backfill is generous: one year from now for invoices, 90 days for
testimonial requests.

Revision ID: 018
Revises: 017
Create Date: 2026-07-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.add_column(
            sa.Column("view_token_expires_at", sa.DateTime(), nullable=True)
        )
    with op.batch_alter_table("testimonials") as batch_op:
        batch_op.add_column(
            sa.Column("request_token_expires_at", sa.DateTime(), nullable=True)
        )

    # Backfill: give live links a generous window from today rather than
    # breaking anything already sitting in a client's inbox. Dates are computed
    # in Python so SQLite and Postgres behave identically.
    from datetime import datetime, timedelta

    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE invoices SET view_token_expires_at = :expiry "
            "WHERE view_token_expires_at IS NULL"
        ),
        {"expiry": datetime.utcnow() + timedelta(days=365)},
    )
    conn.execute(
        sa.text(
            "UPDATE testimonials SET request_token_expires_at = :expiry "
            "WHERE request_token_expires_at IS NULL AND submitted_at IS NULL"
        ),
        {"expiry": datetime.utcnow() + timedelta(days=90)},
    )


def downgrade() -> None:
    with op.batch_alter_table("testimonials") as batch_op:
        batch_op.drop_column("request_token_expires_at")
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.drop_column("view_token_expires_at")
