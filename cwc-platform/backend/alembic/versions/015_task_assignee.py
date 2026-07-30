"""Team workspace: real task assignee

tasks.assigned_to is free text and can't be queried by user, so My Tasks,
workload and notifications had nothing to key off. assignee_id is the real
reference; assigned_to stays for legacy rows.

Revision ID: 015
Revises: 014
Create Date: 2026-07-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "015"
down_revision: Union[str, None] = "014"
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
    if _column_exists("tasks", "assignee_id"):
        return
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("assignee_id", sa.String(36), nullable=True))
        batch_op.create_index("ix_tasks_assignee_id", ["assignee_id"])
        batch_op.create_foreign_key(
            "fk_tasks_assignee_id_users", "users", ["assignee_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_constraint("fk_tasks_assignee_id_users", type_="foreignkey")
        batch_op.drop_index("ix_tasks_assignee_id")
        batch_op.drop_column("assignee_id")
