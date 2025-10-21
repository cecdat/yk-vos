"""add cdr hash and gateway columns

Revision ID: 0003_add_cdr_hash
Revises: 0002_add_cdrs
Create Date: 2025-10-21 00:00:00.000002

"""
from alembic import op
import sqlalchemy as sa

revision = '0003_add_cdr_hash'
down_revision = '0002_add_cdrs'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('cdrs') as batch_op:
        batch_op.add_column(sa.Column('caller_gateway', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('callee_gateway', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('end_time', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('disposition', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('hash', sa.String(length=32), nullable=True))
        batch_op.create_index('ix_cdrs_vos_hash', ['vos_id', 'hash'], unique=False)

def downgrade():
    with op.batch_alter_table('cdrs') as batch_op:
        batch_op.drop_index('ix_cdrs_vos_hash')
        batch_op.drop_column('hash')
        batch_op.drop_column('disposition')
        batch_op.drop_column('end_time')
        batch_op.drop_column('callee_gateway')
        batch_op.drop_column('caller_gateway')
