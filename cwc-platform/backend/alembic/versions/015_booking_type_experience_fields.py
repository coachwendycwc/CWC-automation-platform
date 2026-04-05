"""booking type experience fields

Revision ID: 015_booking_type_experience_fields
Revises: 014_booking_page_banner
Create Date: 2026-04-04
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "015_booking_type_experience_fields"
down_revision = "014_booking_page_banner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("booking_types") as batch_op:
        batch_op.add_column(sa.Column("show_price_on_booking_page", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("location_type", sa.String(length=30), nullable=False, server_default="zoom"))
        batch_op.add_column(sa.Column("location_details", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("post_booking_instructions", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("intake_questions", sa.JSON(), nullable=False, server_default="[]"))

    with op.batch_alter_table("bookings") as batch_op:
        batch_op.add_column(sa.Column("intake_responses", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("bookings") as batch_op:
        batch_op.drop_column("intake_responses")

    with op.batch_alter_table("booking_types") as batch_op:
        batch_op.drop_column("intake_questions")
        batch_op.drop_column("post_booking_instructions")
        batch_op.drop_column("location_details")
        batch_op.drop_column("location_type")
        batch_op.drop_column("show_price_on_booking_page")
