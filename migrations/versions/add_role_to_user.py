"""add role to user

Revision ID: add_role_to_user
Revises: 8b0061102779
Create Date: 2026-02-01 23:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_role_to_user'
down_revision = '8b0061102779'
branch_labels = None
depends_on = None


def upgrade():
    # Add role column with default 'user'
    op.add_column('user', sa.Column('role', sa.String(length=20), nullable=False, server_default='user'))


def downgrade():
    op.drop_column('user', 'role')
