"""Track where our own copy of a recording lives

A Zoom download URL is not ownership: it stops working the moment the
recording is deleted from Zoom. These columns record where WE stored the
media, so the Zoom copy can be purged without losing the session.

Revision ID: 019
Revises: 018
Create Date: 2026-07-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return False
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if _column_exists("fathom_webhooks", "archived_url"):
        return
    with op.batch_alter_table("fathom_webhooks") as batch_op:
        batch_op.add_column(sa.Column("archived_url", sa.String(500), nullable=True))
        batch_op.add_column(sa.Column("archived_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("archived_bytes", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("archived_sha256", sa.String(64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("fathom_webhooks") as batch_op:
        batch_op.drop_column("archived_sha256")
        batch_op.drop_column("archived_bytes")
        batch_op.drop_column("archived_at")
        batch_op.drop_column("archived_url")
