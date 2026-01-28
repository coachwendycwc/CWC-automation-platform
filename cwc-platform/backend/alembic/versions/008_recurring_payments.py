"""Add recurring payments tables

Revision ID: 008
Revises: 007
Create Date: 2024-12-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create stripe_customers table
    op.create_table(
        'stripe_customers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contact_id', sa.String(36), sa.ForeignKey('contacts.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('stripe_customer_id', sa.String(100), unique=True, nullable=False),
        sa.Column('default_payment_method_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_stripe_customers_contact_id', 'stripe_customers', ['contact_id'])
    op.create_index('ix_stripe_customers_stripe_customer_id', 'stripe_customers', ['stripe_customer_id'])

    # Create stripe_products table
    op.create_table(
        'stripe_products',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('stripe_product_id', sa.String(100), unique=True, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_stripe_products_stripe_product_id', 'stripe_products', ['stripe_product_id'])

    # Create stripe_prices table
    op.create_table(
        'stripe_prices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('stripe_products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stripe_price_id', sa.String(100), unique=True, nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='usd'),
        sa.Column('interval', sa.String(20), nullable=False),
        sa.Column('interval_count', sa.Integer(), nullable=False, default=1),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_stripe_prices_product_id', 'stripe_prices', ['product_id'])
    op.create_index('ix_stripe_prices_stripe_price_id', 'stripe_prices', ['stripe_price_id'])

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contact_id', sa.String(36), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('stripe_customer_id', sa.String(36), sa.ForeignKey('stripe_customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stripe_price_id', sa.String(36), sa.ForeignKey('stripe_prices.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(100), unique=True, nullable=False),
        sa.Column('status', sa.String(30), nullable=False, default='active'),
        sa.Column('current_period_start', sa.DateTime(), nullable=False),
        sa.Column('current_period_end', sa.DateTime(), nullable=False),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, default=False),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('trial_start', sa.DateTime(), nullable=True),
        sa.Column('trial_end', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_subscriptions_contact_id', 'subscriptions', ['contact_id'])
    op.create_index('ix_subscriptions_stripe_subscription_id', 'subscriptions', ['stripe_subscription_id'])
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])

    # Create recurring_invoices table
    op.create_table(
        'recurring_invoices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contact_id', sa.String(36), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('line_items', sa.JSON(), nullable=False, default=list),
        sa.Column('subtotal', sa.Numeric(12, 2), nullable=False, default=0),
        sa.Column('tax_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('tax_amount', sa.Numeric(12, 2), nullable=False, default=0),
        sa.Column('discount_amount', sa.Numeric(12, 2), nullable=False, default=0),
        sa.Column('total', sa.Numeric(12, 2), nullable=False, default=0),
        sa.Column('payment_terms', sa.String(20), nullable=False, default='net_30'),
        sa.Column('memo', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('frequency', sa.String(20), nullable=False, default='monthly'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('next_invoice_date', sa.Date(), nullable=False),
        sa.Column('last_generated_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('auto_send', sa.Boolean(), nullable=False, default=False),
        sa.Column('send_days_before', sa.Integer(), nullable=False, default=0),
        sa.Column('invoices_generated', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_recurring_invoices_contact_id', 'recurring_invoices', ['contact_id'])
    op.create_index('ix_recurring_invoices_next_invoice_date', 'recurring_invoices', ['next_invoice_date'])
    op.create_index('ix_recurring_invoices_is_active', 'recurring_invoices', ['is_active'])

    # Add new columns to invoices table
    op.add_column('invoices', sa.Column('subscription_id', sa.String(36), sa.ForeignKey('subscriptions.id', ondelete='SET NULL'), nullable=True))
    op.add_column('invoices', sa.Column('recurring_invoice_id', sa.String(36), sa.ForeignKey('recurring_invoices.id', ondelete='SET NULL'), nullable=True))
    op.add_column('invoices', sa.Column('stripe_invoice_id', sa.String(100), nullable=True))
    op.create_index('ix_invoices_subscription_id', 'invoices', ['subscription_id'])
    op.create_index('ix_invoices_recurring_invoice_id', 'invoices', ['recurring_invoice_id'])


def downgrade() -> None:
    # Remove columns from invoices table
    op.drop_index('ix_invoices_recurring_invoice_id', 'invoices')
    op.drop_index('ix_invoices_subscription_id', 'invoices')
    op.drop_column('invoices', 'stripe_invoice_id')
    op.drop_column('invoices', 'recurring_invoice_id')
    op.drop_column('invoices', 'subscription_id')

    # Drop recurring_invoices table
    op.drop_index('ix_recurring_invoices_is_active', 'recurring_invoices')
    op.drop_index('ix_recurring_invoices_next_invoice_date', 'recurring_invoices')
    op.drop_index('ix_recurring_invoices_contact_id', 'recurring_invoices')
    op.drop_table('recurring_invoices')

    # Drop subscriptions table
    op.drop_index('ix_subscriptions_status', 'subscriptions')
    op.drop_index('ix_subscriptions_stripe_subscription_id', 'subscriptions')
    op.drop_index('ix_subscriptions_contact_id', 'subscriptions')
    op.drop_table('subscriptions')

    # Drop stripe_prices table
    op.drop_index('ix_stripe_prices_stripe_price_id', 'stripe_prices')
    op.drop_index('ix_stripe_prices_product_id', 'stripe_prices')
    op.drop_table('stripe_prices')

    # Drop stripe_products table
    op.drop_index('ix_stripe_products_stripe_product_id', 'stripe_products')
    op.drop_table('stripe_products')

    # Drop stripe_customers table
    op.drop_index('ix_stripe_customers_stripe_customer_id', 'stripe_customers')
    op.drop_index('ix_stripe_customers_contact_id', 'stripe_customers')
    op.drop_table('stripe_customers')
