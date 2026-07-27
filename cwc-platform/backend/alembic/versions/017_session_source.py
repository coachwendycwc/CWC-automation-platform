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


def upgrade() -> None:
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
