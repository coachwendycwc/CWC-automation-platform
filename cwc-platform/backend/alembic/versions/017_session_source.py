"""Session recordings can come from Zoom, not just Fathom

The fathom_webhooks table predates having more than one source. Zoom
cloud-recording exports land in the same table (it is what the client portal
reads), so rows need to say where they came from.

Revision ID: 017
Revises: 016
Create Date: 2026-07-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def _column_exists(table: str, column: str) -> bool:
    """Databases built by create_all before schema was migration-managed
    already have some of these columns; adding them again would fail."""
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return False
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if _column_exists("fathom_webhooks", "source"):
        return
    with op.batch_alter_table("fathom_webhooks") as batch_op:
        batch_op.add_column(
            sa.Column(
                "source",
                sa.String(20),
                nullable=False,
                server_default="fathom",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("fathom_webhooks") as batch_op:
        batch_op.drop_column("source")
