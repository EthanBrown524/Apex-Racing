"""add gps_image to circuits

Revision ID: a1b2c3d4e5f6
Revises: c254d08a60f5
Create Date: 2026-05-14 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = 'c254d08a60f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('circuits', sa.Column('gps_image', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('circuits', 'gps_image')