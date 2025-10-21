"""add cdrs table

Revision ID: 0002_add_cdrs
Revises: 0001_initial
Create Date: 2025-10-21 00:00:00.000001

"""
from alembic import op
import sqlalchemy as sa

revision = '0002_add_cdrs'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'cdrs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vos_id', sa.Integer(), nullable=True),
        sa.Column('caller', sa.String(length=64), nullable=True),
        sa.Column('callee', sa.String(length=64), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Numeric(10, 4), nullable=True),
        sa.Column('raw', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cdrs_id'), 'cdrs', ['id'], unique=False)
    op.create_index(op.f('ix_cdrs_vos_id'), 'cdrs', ['vos_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_cdrs_vos_id'), table_name='cdrs')
    op.drop_index(op.f('ix_cdrs_id'), table_name='cdrs')
    op.drop_table('cdrs')

