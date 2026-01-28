"""icf_certification_progress

Revision ID: c5e8f12a3b4d
Revises: b4bdf53e29a0
Create Date: 2026-01-03 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5e8f12a3b4d'
down_revision: Union[str, None] = 'b4bdf53e29a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'icf_certification_progress',
        sa.Column('id', sa.String(36), primary_key=True),

        # ACC Training (60 hours required)
        sa.Column('acc_training_hours', sa.Float, default=0),
        sa.Column('acc_training_provider', sa.String(255), nullable=True),
        sa.Column('acc_training_completed', sa.Boolean, default=False),
        sa.Column('acc_training_completion_date', sa.DateTime, nullable=True),
        sa.Column('acc_training_certificate_url', sa.String(500), nullable=True),

        # PCC Training (125 hours required)
        sa.Column('pcc_training_hours', sa.Float, default=0),
        sa.Column('pcc_training_provider', sa.String(255), nullable=True),
        sa.Column('pcc_training_completed', sa.Boolean, default=False),
        sa.Column('pcc_training_completion_date', sa.DateTime, nullable=True),
        sa.Column('pcc_training_certificate_url', sa.String(500), nullable=True),

        # ACC Mentor Coaching (10 hours required)
        sa.Column('acc_mentor_hours', sa.Float, default=0),
        sa.Column('acc_mentor_individual_hours', sa.Float, default=0),
        sa.Column('acc_mentor_group_hours', sa.Float, default=0),
        sa.Column('acc_mentor_name', sa.String(255), nullable=True),
        sa.Column('acc_mentor_credential', sa.String(20), nullable=True),
        sa.Column('acc_mentor_completed', sa.Boolean, default=False),

        # PCC Mentor Coaching (10 hours required)
        sa.Column('pcc_mentor_hours', sa.Float, default=0),
        sa.Column('pcc_mentor_individual_hours', sa.Float, default=0),
        sa.Column('pcc_mentor_group_hours', sa.Float, default=0),
        sa.Column('pcc_mentor_name', sa.String(255), nullable=True),
        sa.Column('pcc_mentor_credential', sa.String(20), nullable=True),
        sa.Column('pcc_mentor_completed', sa.Boolean, default=False),

        # ACC Exam
        sa.Column('acc_exam_passed', sa.Boolean, default=False),
        sa.Column('acc_exam_date', sa.DateTime, nullable=True),
        sa.Column('acc_exam_score', sa.Integer, nullable=True),

        # PCC Exam
        sa.Column('pcc_exam_passed', sa.Boolean, default=False),
        sa.Column('pcc_exam_date', sa.DateTime, nullable=True),
        sa.Column('pcc_exam_score', sa.Integer, nullable=True),

        # ACC Application/Credential
        sa.Column('acc_applied', sa.Boolean, default=False),
        sa.Column('acc_application_date', sa.DateTime, nullable=True),
        sa.Column('acc_credential_received', sa.Boolean, default=False),
        sa.Column('acc_credential_date', sa.DateTime, nullable=True),
        sa.Column('acc_credential_number', sa.String(50), nullable=True),
        sa.Column('acc_expiration_date', sa.DateTime, nullable=True),

        # PCC Application/Credential
        sa.Column('pcc_applied', sa.Boolean, default=False),
        sa.Column('pcc_application_date', sa.DateTime, nullable=True),
        sa.Column('pcc_credential_received', sa.Boolean, default=False),
        sa.Column('pcc_credential_date', sa.DateTime, nullable=True),
        sa.Column('pcc_credential_number', sa.String(50), nullable=True),
        sa.Column('pcc_expiration_date', sa.DateTime, nullable=True),

        # Notes
        sa.Column('notes', sa.Text, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('icf_certification_progress')
