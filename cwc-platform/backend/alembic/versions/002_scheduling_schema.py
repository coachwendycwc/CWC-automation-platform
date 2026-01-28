"""Scheduling schema - Phase 2

Revision ID: 002
Revises: 001
Create Date: 2025-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Booking types table
    op.create_table(
        "booking_types",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("duration_minutes", sa.Integer, nullable=False, server_default="60"),
        sa.Column("color", sa.String(7), nullable=False, server_default="#3B82F6"),
        sa.Column("price", sa.Numeric(10, 2)),
        sa.Column("buffer_before", sa.Integer, nullable=False, server_default="0"),
        sa.Column("buffer_after", sa.Integer, nullable=False, server_default="15"),
        sa.Column("min_notice_hours", sa.Integer, nullable=False, server_default="24"),
        sa.Column("max_advance_days", sa.Integer, nullable=False, server_default="60"),
        sa.Column("max_per_day", sa.Integer),
        sa.Column("requires_confirmation", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Availabilities table (weekly recurring)
    op.create_table(
        "availabilities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("day_of_week", sa.Integer, nullable=False),  # 0=Monday, 6=Sunday
        sa.Column("start_time", sa.String(5), nullable=False),  # "09:00"
        sa.Column("end_time", sa.String(5), nullable=False),  # "17:00"
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Availability overrides table (specific dates)
    op.create_table(
        "availability_overrides",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("start_time", sa.String(5)),  # null = blocked all day
        sa.Column("end_time", sa.String(5)),
        sa.Column("is_available", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("reason", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Bookings table
    op.create_table(
        "bookings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "booking_type_id",
            sa.String(36),
            sa.ForeignKey("booking_types.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "contact_id",
            sa.String(36),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("start_time", sa.DateTime, nullable=False, index=True),
        sa.Column("end_time", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("google_event_id", sa.String(255)),
        sa.Column("notes", sa.Text),
        sa.Column("cancellation_reason", sa.Text),
        sa.Column("cancelled_at", sa.DateTime),
        sa.Column("cancelled_by", sa.String(10)),  # "client" or "host"
        sa.Column("confirmation_token", sa.String(64), unique=True, nullable=False),
        sa.Column("reminder_sent_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("bookings")
    op.drop_table("availability_overrides")
    op.drop_table("availabilities")
    op.drop_table("booking_types")
