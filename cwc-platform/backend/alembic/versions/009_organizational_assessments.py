"""Add organizational assessments table

Revision ID: 009
Revises: 008
Create Date: 2024-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'organizational_assessments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contact_id', sa.String(36), sa.ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),

        # Section 1: Contact Information
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('title_role', sa.String(200), nullable=False),
        sa.Column('organization_name', sa.String(200), nullable=False),
        sa.Column('work_email', sa.String(200), nullable=False),
        sa.Column('phone_number', sa.String(50), nullable=True),
        sa.Column('organization_website', sa.String(300), nullable=True),

        # Section 2: Areas of Interest
        sa.Column('areas_of_interest', sa.JSON(), nullable=False, default=list),
        sa.Column('areas_of_interest_other', sa.Text(), nullable=True),

        # Section 3: Goals and Needs
        sa.Column('desired_outcomes', sa.JSON(), nullable=False, default=list),
        sa.Column('desired_outcomes_other', sa.Text(), nullable=True),
        sa.Column('current_challenge', sa.Text(), nullable=True),

        # Audience
        sa.Column('primary_audience', sa.JSON(), nullable=False, default=list),
        sa.Column('primary_audience_other', sa.Text(), nullable=True),
        sa.Column('participant_count', sa.String(20), nullable=True),

        # Format
        sa.Column('preferred_format', sa.String(20), nullable=True),
        sa.Column('location', sa.String(200), nullable=True),

        # Section 4: Budget and Timeline
        sa.Column('budget_range', sa.String(30), nullable=True),
        sa.Column('specific_budget', sa.String(100), nullable=True),
        sa.Column('ideal_timeline', sa.String(30), nullable=True),
        sa.Column('specific_date', sa.String(200), nullable=True),

        # Section 5: Decision Process
        sa.Column('decision_makers', sa.JSON(), nullable=False, default=list),
        sa.Column('decision_makers_other', sa.Text(), nullable=True),
        sa.Column('decision_stage', sa.String(30), nullable=True),
        sa.Column('decision_stage_other', sa.Text(), nullable=True),

        # Section 6: Additional Context
        sa.Column('success_definition', sa.Text(), nullable=True),
        sa.Column('accessibility_needs', sa.Text(), nullable=True),

        # Tracking
        sa.Column('booking_id', sa.String(36), sa.ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, default='submitted'),

        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Indexes
    op.create_index('ix_organizational_assessments_status', 'organizational_assessments', ['status'])
    op.create_index('ix_organizational_assessments_work_email', 'organizational_assessments', ['work_email'])
    op.create_index('ix_organizational_assessments_organization_name', 'organizational_assessments', ['organization_name'])


def downgrade() -> None:
    op.drop_index('ix_organizational_assessments_organization_name', 'organizational_assessments')
    op.drop_index('ix_organizational_assessments_work_email', 'organizational_assessments')
    op.drop_index('ix_organizational_assessments_status', 'organizational_assessments')
    op.drop_table('organizational_assessments')
