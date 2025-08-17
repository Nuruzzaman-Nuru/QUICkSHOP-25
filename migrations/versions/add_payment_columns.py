"""Add payment columns to order table

Revision ID: add_payment_cols
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = 'add_payment_cols'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add payment-related columns to the order table
    op.add_column('order', sa.Column('payment_method', sa.String(20), nullable=False, server_default='cod'))
    op.add_column('order', sa.Column('payment_status', sa.String(20), nullable=False, server_default='pending'))
    op.add_column('order', sa.Column('payment_details', sa.JSON, nullable=True))
    op.add_column('order', sa.Column('payment_transaction_id', sa.String(100), nullable=True))


def downgrade():
    # Remove payment-related columns from the order table
    op.drop_column('order', 'payment_transaction_id')
    op.drop_column('order', 'payment_details')
    op.drop_column('order', 'payment_status')
    op.drop_column('order', 'payment_method')