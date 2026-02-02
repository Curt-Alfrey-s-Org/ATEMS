"""add return_by column to checkout_history

Revision ID: add_return_by
Revises: 8b0061102779
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_return_by'
down_revision = 'add_role_to_user'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # SQLite: avoid duplicate column if table was created by create_all()
    if conn.dialect.name == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(checkout_history)"))
        cols = [row[1] for row in result]
        if 'return_by' in cols:
            return
    op.add_column('checkout_history', sa.Column('return_by', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('checkout_history', 'return_by')
