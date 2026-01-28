"""Projects & Tasks schema - Phase 5

Revision ID: 005
Revises: 004
Create Date: 2025-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Project templates table (for reusable project structures)
    op.create_table(
        "project_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("project_type", sa.String(50), nullable=False, server_default="coaching"),
        sa.Column("default_duration_days", sa.Integer, nullable=False, server_default="30"),
        sa.Column("estimated_hours", sa.Numeric(8, 2)),
        # Template tasks stored as JSON array
        # Structure: [{"title": str, "description": str|None, "estimated_hours": float|None, "order_index": int}]
        sa.Column("task_templates", sa.JSON, server_default="[]"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_number", sa.String(20), unique=True, nullable=False),
        # Client linkage
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
        # Basic info
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("project_type", sa.String(50), nullable=False, server_default="coaching", index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="planning", index=True),
        # Timeline
        sa.Column("start_date", sa.Date),
        sa.Column("target_end_date", sa.Date),
        sa.Column("actual_end_date", sa.Date),
        # Budget & Hours
        sa.Column("budget_amount", sa.Numeric(12, 2)),
        sa.Column("estimated_hours", sa.Numeric(8, 2)),
        # Links to other entities
        sa.Column(
            "linked_contract_id",
            sa.String(36),
            sa.ForeignKey("contracts.id", ondelete="SET NULL"),
            index=True,
        ),
        sa.Column(
            "linked_invoice_id",
            sa.String(36),
            sa.ForeignKey("invoices.id", ondelete="SET NULL"),
            index=True,
        ),
        sa.Column(
            "template_id",
            sa.String(36),
            sa.ForeignKey("project_templates.id", ondelete="SET NULL"),
            index=True,
        ),
        # Progress (computed from tasks)
        sa.Column("progress_percent", sa.Integer, nullable=False, server_default="0"),
        # Public access
        sa.Column("view_token", sa.String(64), unique=True, nullable=False),
        sa.Column("client_visible", sa.Boolean, nullable=False, server_default="0"),
        # Timestamps
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_number", sa.String(20), unique=True, nullable=False),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Task info
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="todo", index=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        # Assignment
        sa.Column("assigned_to", sa.String(255)),
        # Timeline
        sa.Column("due_date", sa.Date),
        sa.Column("completed_at", sa.DateTime),
        # Time tracking
        sa.Column("estimated_hours", sa.Numeric(8, 2)),
        sa.Column("actual_hours", sa.Numeric(8, 2), nullable=False, server_default="0"),
        # Ordering & dependencies (for Kanban drag/drop)
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "depends_on_task_id",
            sa.String(36),
            sa.ForeignKey("tasks.id", ondelete="SET NULL"),
        ),
        # Subtasks (self-referential)
        sa.Column(
            "parent_task_id",
            sa.String(36),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
        ),
        # Notes
        sa.Column("notes", sa.Text),
        # Timestamps
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Time entries table
    op.create_table(
        "time_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("description", sa.Text),
        sa.Column("hours", sa.Numeric(8, 2), nullable=False),
        sa.Column("entry_date", sa.Date, nullable=False),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Project activity logs table
    op.create_table(
        "project_activity_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("tasks.id", ondelete="SET NULL"),
            index=True,
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("actor", sa.String(255)),
        sa.Column("details", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Update contracts table: add FK for linked_project_id
    # SQLite doesn't support ALTER COLUMN to add FK, so we just create an index
    # The FK constraint is defined in the model and enforced at application level
    op.create_index(
        "ix_contracts_linked_project_id",
        "contracts",
        ["linked_project_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_contracts_linked_project_id", table_name="contracts")
    op.drop_table("project_activity_logs")
    op.drop_table("time_entries")
    op.drop_table("tasks")
    op.drop_table("projects")
    op.drop_table("project_templates")
