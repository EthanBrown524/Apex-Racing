"""add circuit gps image

Revision ID: 20260514_add_circuit_gps_image
Revises: c254d08a60f5
Create Date: 2026-05-14
"""
from alembic import op
import sqlalchemy as sa


revision = "20260514_add_circuit_gps_image"
down_revision = "c254d08a60f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("circuits", sa.Column("gps_image", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("circuits", "gps_image")
