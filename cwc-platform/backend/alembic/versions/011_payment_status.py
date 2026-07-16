"""Add nullable status column to payments

Records the outcome of a payment (completed, failed, refunded). Added because
the Stripe webhook handlers set a payment status but the payments table had no
column for it, causing every real Stripe payment write to fail. Nullable with
no backfill: existing manual payment rows simply have status = NULL.

Revision ID: 011
Revises: c5e8f12a3b4d
Create Date: 2026-07-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "011"
down_revision: Union[str, None] = "c5e8f12a3b4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch_alter_table keeps this portable across PostgreSQL (production) and
    # SQLite (tests/dev), which cannot ALTER TABLE ADD COLUMN directly.
    with op.batch_alter_table("payments") as batch_op:
        batch_op.add_column(sa.Column("status", sa.String(20), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("payments") as batch_op:
        batch_op.drop_column("status")
