"""Track which calendar connection owns a booking event

Revision ID: 013_booking_calendar_connection
Revises: 012_booking_page_branding
Create Date: 2026-04-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "013_booking_calendar_connection"
down_revision: Union[str, None] = "012_booking_page_branding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("bookings")}

    if "calendar_connection_id" not in columns:
        op.add_column(
            "bookings",
            sa.Column("calendar_connection_id", sa.String(length=36), nullable=True),
        )

    if bind.dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_bookings_calendar_connection_id",
            "bookings",
            "calendar_connections",
            ["calendar_connection_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name != "sqlite":
        op.drop_constraint("fk_bookings_calendar_connection_id", "bookings", type_="foreignkey")
    op.drop_column("bookings", "calendar_connection_id")
