"""Create the tables no migration ever created

The schema had drifted into two sources of truth: the models defined 52 tables
but the migration chain only ever created 34. The other 18 — the whole client
portal, testimonials, offboarding, bookkeeping, contractors — existed only
because someone ran `Base.metadata.create_all()` on a dev machine. Nothing
wrote down how to build them.

The consequence: `alembic upgrade head` against an empty database died at
migration 012 ("relation contractors does not exist"), so a fresh environment
(a new AWS deploy, a new developer, a restored backup) could not be built at
all.

This migration is the catch-up. Every table is created ONLY IF ABSENT, so it
is a no-op on databases where create_all already made them, and it does the
real work on a fresh one. Definitions are generated from the models, so they
match by construction rather than by hand-transcription.

After this, migrations are the single source of truth for schema. Do not use
create_all again.

Revision ID: 011a
Revises: 011

Deliberately inserted between 011 and 012 rather than appended at the end:
migration 012 ALTERs `contractors`, so these tables must exist before it runs
or a fresh database still fails there.
Create Date: 2026-07-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "011a"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _create_if_absent(name: str, *columns) -> None:
    """Create a table only when it isn't already there.

    Databases that predate this migration already have these tables from
    create_all; a fresh database does not. Both must end up in the same place.
    """
    if name in _existing_tables():
        return
    op.create_table(name, *columns)


def _index_if_absent(name: str, table: str, columns: list[str], unique: bool = False) -> None:
    if table not in _existing_tables():
        return
    existing = {ix["name"] for ix in sa.inspect(op.get_bind()).get_indexes(table)}
    if name in existing:
        return
    op.create_index(name, table, columns, unique=unique)


def upgrade() -> None:
    _create_if_absent(
        "contractors",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('business_name', sa.String(length=200)),
            sa.Column('email', sa.String(length=255)),
            sa.Column('phone', sa.String(length=20)),
            # Pre-012 shape on purpose: this migration recreates the table as it
        # existed BEFORE 012 encrypted the tax id, so 012 still performs its
        # real work (add ciphertext column, encrypt, drop plaintext) instead of
        # colliding with a column that already exists.
        sa.Column('tax_id', sa.String(length=20)),
            sa.Column('tax_id_type', sa.String(length=10), nullable=False),
            sa.Column('w9_on_file', sa.Boolean(), nullable=False),
            sa.Column('w9_received_date', sa.Date()),
            sa.Column('address_line1', sa.String(length=200)),
            sa.Column('address_line2', sa.String(length=200)),
            sa.Column('city', sa.String(length=100)),
            sa.Column('state', sa.String(length=50)),
            sa.Column('zip_code', sa.String(length=20)),
            sa.Column('service_type', sa.String(length=100)),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "expense_categories",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text()),
            sa.Column('color', sa.String(length=7), nullable=False),
            sa.Column('icon', sa.String(length=50)),
            sa.Column('is_tax_deductible', sa.Boolean(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "recurring_expenses",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('description', sa.String(length=500), nullable=False),
            sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('vendor', sa.String(length=200)),
            sa.Column('category_id', sa.String(length=36), sa.ForeignKey('expense_categories.id', ondelete='SET NULL')),
            sa.Column('frequency', sa.String(length=20), nullable=False),
            sa.Column('start_date', sa.Date(), nullable=False),
            sa.Column('end_date', sa.Date()),
            sa.Column('next_due_date', sa.Date(), nullable=False),
            sa.Column('last_generated_date', sa.Date()),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('auto_create', sa.Boolean(), nullable=False),
            sa.Column('reminder_days', sa.Integer(), nullable=False),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "expenses",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('description', sa.String(length=500), nullable=False),
            sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('expense_date', sa.Date(), nullable=False),
            sa.Column('category_id', sa.String(length=36), sa.ForeignKey('expense_categories.id', ondelete='SET NULL')),
            sa.Column('vendor', sa.String(length=200)),
            sa.Column('payment_method', sa.String(length=50), nullable=False),
            sa.Column('reference', sa.String(length=100)),
            sa.Column('receipt_url', sa.String(length=500)),
            sa.Column('is_recurring', sa.Boolean(), nullable=False),
            sa.Column('recurring_expense_id', sa.String(length=36), sa.ForeignKey('recurring_expenses.id', ondelete='SET NULL')),
            sa.Column('is_tax_deductible', sa.Boolean(), nullable=False),
            sa.Column('tax_year', sa.Integer(), nullable=False),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "contractor_payments",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('contractor_id', sa.String(length=36), sa.ForeignKey('contractors.id', ondelete='CASCADE'), nullable=False),
            sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('payment_date', sa.Date(), nullable=False),
            sa.Column('description', sa.String(length=500), nullable=False),
            sa.Column('payment_method', sa.String(length=50), nullable=False),
            sa.Column('reference', sa.String(length=100)),
            sa.Column('expense_id', sa.String(length=36), sa.ForeignKey('expenses.id', ondelete='SET NULL')),
            sa.Column('invoice_number', sa.String(length=50)),
            sa.Column('invoice_url', sa.String(length=500)),
            sa.Column('tax_year', sa.Integer(), nullable=False),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "testimonials",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id', ondelete='SET NULL')),
            sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='SET NULL')),
            sa.Column('video_url', sa.String(length=500)),
            sa.Column('video_public_id', sa.String(length=255)),
            sa.Column('video_duration_seconds', sa.Integer()),
            sa.Column('thumbnail_url', sa.String(length=500)),
            sa.Column('quote', sa.Text()),
            sa.Column('transcript', sa.Text()),
            sa.Column('author_name', sa.String(length=255), nullable=False),
            sa.Column('author_title', sa.String(length=255)),
            sa.Column('author_company', sa.String(length=255)),
            sa.Column('author_photo_url', sa.String(length=500)),
            sa.Column('permission_granted', sa.Boolean(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('featured', sa.Boolean(), nullable=False),
            sa.Column('display_order', sa.Integer(), nullable=False),
            sa.Column('request_token', sa.String(length=64), nullable=False, unique=True),
        # Omitted on purpose: migration 018 adds this column. Creating it here
        # too would make 018 fail on a fresh database.
        # sa.Column('request_token_expires_at', sa.DateTime()),
            sa.Column('request_sent_at', sa.DateTime()),
            sa.Column('submitted_at', sa.DateTime()),
            sa.Column('reviewed_at', sa.DateTime()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "client_sessions",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id'), nullable=False),
            sa.Column('token', sa.String(length=64), nullable=False, unique=True),
            sa.Column('token_used_at', sa.DateTime()),
            sa.Column('session_token', sa.String(length=500), unique=True),
            sa.Column('email_sent_at', sa.DateTime()),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('ip_address', sa.String(length=45)),
            sa.Column('user_agent', sa.Text()),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    _index_if_absent("ix_client_sessions_contact_id", "client_sessions", ['contact_id'], unique=False)
    _index_if_absent("ix_client_sessions_token", "client_sessions", ['token'], unique=True)
    _create_if_absent(
        "client_notes",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('direction', sa.String(length=20), nullable=False),
            sa.Column('parent_id', sa.String(length=36), sa.ForeignKey('client_notes.id', ondelete='CASCADE')),
            sa.Column('is_read', sa.Boolean(), nullable=False),
            sa.Column('read_at', sa.DateTime()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    _index_if_absent("ix_client_notes_contact_id", "client_notes", ['contact_id'], unique=False)
    _create_if_absent(
        "client_goals",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text()),
            sa.Column('category', sa.String(length=50)),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('target_date', sa.Date()),
            sa.Column('completed_at', sa.DateTime()),
            sa.Column('target_reminder_sent_at', sa.DateTime()),
            sa.Column('progress_checkin_sent_at', sa.DateTime()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "goal_milestones",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('goal_id', sa.String(length=36), sa.ForeignKey('client_goals.id', ondelete='CASCADE'), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text()),
            sa.Column('target_date', sa.Date()),
            sa.Column('is_completed', sa.Boolean(), nullable=False),
            sa.Column('completed_at', sa.DateTime()),
            sa.Column('sort_order', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "client_action_items",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
            sa.Column('session_id', sa.String(length=36), sa.ForeignKey('fathom_webhooks.id', ondelete='SET NULL')),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text()),
            sa.Column('due_date', sa.Date()),
            sa.Column('priority', sa.String(length=20), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('completed_at', sa.DateTime()),
            sa.Column('reminder_sent_at', sa.DateTime()),
            sa.Column('overdue_reminder_sent_at', sa.DateTime()),
            sa.Column('created_by', sa.String(length=50), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    _index_if_absent("ix_client_action_items_contact_id", "client_action_items", ['contact_id'], unique=False)
    _create_if_absent(
        "client_contents",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text()),
            sa.Column('content_type', sa.String(length=50), nullable=False),
            sa.Column('file_url', sa.String(length=500)),
            sa.Column('file_name', sa.String(length=255)),
            sa.Column('file_size', sa.Integer()),
            sa.Column('mime_type', sa.String(length=100)),
            sa.Column('external_url', sa.String(length=500)),
            sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id', ondelete='CASCADE')),
            sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE')),
            sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='CASCADE')),
            sa.Column('release_date', sa.DateTime()),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('sort_order', sa.Integer(), nullable=False),
            sa.Column('category', sa.String(length=100)),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "portal_audit_logs",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
            sa.Column('action', sa.String(length=50), nullable=False),
            sa.Column('resource_type', sa.String(length=50)),
            sa.Column('resource_id', sa.String(length=36)),
            sa.Column('ip_address', sa.String(length=45)),
            sa.Column('user_agent', sa.Text()),
            sa.Column('details', sa.JSON()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "offboarding_templates",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text()),
            sa.Column('workflow_type', sa.String(length=20), nullable=False),
            sa.Column('checklist_items', sa.JSON(), nullable=False),
            sa.Column('completion_email_subject', sa.String(length=200)),
            sa.Column('completion_email_body', sa.Text()),
            sa.Column('survey_email_subject', sa.String(length=200)),
            sa.Column('survey_email_body', sa.Text()),
            sa.Column('testimonial_email_subject', sa.String(length=200)),
            sa.Column('testimonial_email_body', sa.Text()),
            sa.Column('survey_delay_days', sa.Integer(), nullable=False),
            sa.Column('testimonial_delay_days', sa.Integer(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "offboarding_workflows",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
            sa.Column('workflow_type', sa.String(length=20), nullable=False),
            sa.Column('related_project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='SET NULL')),
            sa.Column('related_contract_id', sa.String(length=36), sa.ForeignKey('contracts.id', ondelete='SET NULL')),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('initiated_at', sa.DateTime(), nullable=False),
            sa.Column('completed_at', sa.DateTime()),
            sa.Column('checklist', sa.JSON(), nullable=False),
            sa.Column('send_survey', sa.Boolean(), nullable=False),
            sa.Column('request_testimonial', sa.Boolean(), nullable=False),
            sa.Column('send_certificate', sa.Boolean(), nullable=False),
            sa.Column('survey_sent_at', sa.DateTime()),
            sa.Column('survey_token', sa.String(length=64), unique=True),
            sa.Column('survey_completed_at', sa.DateTime()),
            sa.Column('survey_response', sa.JSON()),
            sa.Column('testimonial_requested_at', sa.DateTime()),
            sa.Column('testimonial_token', sa.String(length=64), unique=True),
            sa.Column('testimonial_received', sa.Boolean(), nullable=False),
            sa.Column('testimonial_text', sa.Text()),
            sa.Column('testimonial_author_name', sa.String(length=200)),
            sa.Column('testimonial_author_title', sa.String(length=200)),
            sa.Column('testimonial_photo_url', sa.Text()),
            sa.Column('testimonial_permission_granted', sa.Boolean(), nullable=False),
            sa.Column('testimonial_approved', sa.Boolean(), nullable=False),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "offboarding_activities",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('workflow_id', sa.String(length=36), sa.ForeignKey('offboarding_workflows.id', ondelete='CASCADE'), nullable=False),
            sa.Column('action', sa.String(length=50), nullable=False),
            sa.Column('details', sa.JSON()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    _create_if_absent(
        "mileage_rates",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('year', sa.Integer(), nullable=False, unique=True),
            sa.Column('rate_per_mile', sa.Numeric(precision=6, scale=4), nullable=False),
            sa.Column('effective_date', sa.Date(), nullable=False),
            sa.Column('notes', sa.String(length=200)),
    )
    _create_if_absent(
        "mileage_logs",
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('trip_date', sa.Date(), nullable=False),
            sa.Column('description', sa.String(length=500), nullable=False),
            sa.Column('purpose', sa.String(length=50), nullable=False),
            sa.Column('miles', sa.Numeric(precision=8, scale=2), nullable=False),
            sa.Column('rate_per_mile', sa.Numeric(precision=6, scale=4), nullable=False),
            sa.Column('total_deduction', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('start_location', sa.String(length=200)),
            sa.Column('end_location', sa.String(length=200)),
            sa.Column('round_trip', sa.Boolean(), nullable=False),
            sa.Column('contact_id', sa.String(length=36), sa.ForeignKey('contacts.id', ondelete='SET NULL')),
            sa.Column('tax_year', sa.Integer(), nullable=False),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Deliberately a no-op.

    These tables hold real data (client portal sessions, testimonials,
    offboarding records, bookkeeping). Dropping them to "undo" a migration that
    only ever created what should have existed all along would destroy data to
    fix a bookkeeping problem. Roll back the code, not the tables.
    """
    pass
