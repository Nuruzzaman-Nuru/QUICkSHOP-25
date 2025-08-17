"""Add rating fields to Product model and create Review model

Revision ID: add_rating_fields
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add rating fields to Product table
    op.add_column('product', sa.Column('rating', sa.Float(), nullable=True, default=0.0))
    op.add_column('product', sa.Column('rating_count', sa.Integer(), nullable=True, default=0))

    # Create Review table
    op.create_table('review',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('review')
    op.drop_column('product', 'rating_count')
    op.drop_column('product', 'rating')
