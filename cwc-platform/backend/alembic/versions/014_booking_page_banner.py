"""Add booking page banner field to users

Revision ID: 014_booking_page_banner
Revises: 013_booking_calendar_connection
Create Date: 2026-04-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "014_booking_page_banner"
down_revision: Union[str, None] = "013_booking_calendar_connection"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("booking_page_banner_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "booking_page_banner_url")
