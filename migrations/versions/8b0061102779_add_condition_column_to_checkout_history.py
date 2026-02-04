"""add condition column to checkout_history

Revision ID: 8b0061102779
Revises: d20771c3bb27
Create Date: 2026-02-01 22:40:45.922255

"""
from alembic import op
import sqlalchemy as sa


revision = '8b0061102779'
down_revision = 'd20771c3bb27'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('checkout_history', sa.Column('condition', sa.String(length=32), nullable=True))


def downgrade():
    op.drop_column('checkout_history', 'condition')
