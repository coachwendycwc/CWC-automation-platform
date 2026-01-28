"""onboarding_assessments

Revision ID: b4bdf53e29a0
Revises: 010
Create Date: 2026-01-03 15:01:57.113261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4bdf53e29a0'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'onboarding_assessments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contact_id', sa.String(36), sa.ForeignKey('contacts.id', ondelete='CASCADE'), unique=True, nullable=False, index=True),
        sa.Column('token', sa.String(64), unique=True, nullable=False),

        # Section 1: Client Context
        sa.Column('name_pronouns', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('role_title', sa.String(255), nullable=True),
        sa.Column('organization_industry', sa.String(255), nullable=True),
        sa.Column('time_in_role', sa.String(100), nullable=True),
        sa.Column('role_description', sa.Text, nullable=True),
        sa.Column('coaching_motivations', sa.JSON, nullable=True),

        # Section 2: Self Assessment (1-10 ratings)
        sa.Column('confidence_leadership', sa.Integer, nullable=True),
        sa.Column('feeling_respected', sa.Integer, nullable=True),
        sa.Column('clear_goals_short_term', sa.Integer, nullable=True),
        sa.Column('clear_goals_long_term', sa.Integer, nullable=True),
        sa.Column('work_life_balance', sa.Integer, nullable=True),
        sa.Column('stress_management', sa.Integer, nullable=True),
        sa.Column('access_mentors', sa.Integer, nullable=True),
        sa.Column('navigate_bias', sa.Integer, nullable=True),
        sa.Column('communication_effectiveness', sa.Integer, nullable=True),
        sa.Column('taking_up_space', sa.Integer, nullable=True),
        sa.Column('team_advocacy', sa.Integer, nullable=True),
        sa.Column('career_satisfaction', sa.Integer, nullable=True),
        sa.Column('priority_focus_areas', sa.Text, nullable=True),

        # Section 3: Identity & Workplace Experience
        sa.Column('workplace_experience', sa.Text, nullable=True),
        sa.Column('self_doubt_patterns', sa.Text, nullable=True),
        sa.Column('habits_to_shift', sa.Text, nullable=True),

        # Section 4: Goals for Coaching
        sa.Column('coaching_goal', sa.Text, nullable=True),
        sa.Column('success_evidence', sa.Text, nullable=True),
        sa.Column('thriving_vision', sa.Text, nullable=True),

        # Section 5: Wellbeing & Support
        sa.Column('commitment_time', sa.Integer, nullable=True),
        sa.Column('commitment_energy', sa.Integer, nullable=True),
        sa.Column('commitment_focus', sa.Integer, nullable=True),
        sa.Column('potential_barriers', sa.Text, nullable=True),
        sa.Column('support_needed', sa.Text, nullable=True),
        sa.Column('feedback_preference', sa.String(50), nullable=True),
        sa.Column('sensitive_topics', sa.Text, nullable=True),

        # Section 6: Logistics & Preferences
        sa.Column('scheduling_preferences', sa.Text, nullable=True),

        # Tracking
        sa.Column('email_sent_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('onboarding_assessments')
