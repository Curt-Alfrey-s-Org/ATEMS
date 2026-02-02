"""add category to tools

Revision ID: add_category_tools
Revises: 8b0061102779
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_category_tools'
down_revision = '8b0061102779'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tools', sa.Column('category', sa.String(length=64), nullable=True))


def downgrade():
    op.drop_column('tools', 'category')
