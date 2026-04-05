"""booking meeting fields

Revision ID: 016_booking_meeting_fields
Revises: 015_booking_type_experience_fields
Create Date: 2026-04-04
"""

from alembic import op
import sqlalchemy as sa


revision = "016_booking_meeting_fields"
down_revision = "015_booking_type_experience_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("bookings") as batch_op:
        batch_op.add_column(sa.Column("meeting_provider", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("meeting_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("bookings") as batch_op:
        batch_op.drop_column("meeting_url")
        batch_op.drop_column("meeting_provider")
