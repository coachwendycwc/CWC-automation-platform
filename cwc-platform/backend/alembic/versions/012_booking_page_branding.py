"""Add booking page branding fields to users

Revision ID: 012_booking_page_branding
Revises: 011_calendar_connections
Create Date: 2026-04-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "012_booking_page_branding"
down_revision: Union[str, None] = "011_calendar_connections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("booking_page_title", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("booking_page_description", sa.String(1000), nullable=True))
    op.add_column("users", sa.Column("booking_page_brand_color", sa.String(7), nullable=False, server_default="#2A7B8C"))
    op.add_column("users", sa.Column("booking_page_logo_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "booking_page_logo_url")
    op.drop_column("users", "booking_page_brand_color")
    op.drop_column("users", "booking_page_description")
    op.drop_column("users", "booking_page_title")
