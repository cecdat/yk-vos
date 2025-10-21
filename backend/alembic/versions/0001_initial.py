"""initial tables

Revision ID: 0001_initial
Revises: 
Create Date: 2025-10-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('hashed_password', sa.String(length=256), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Create vos_instances table
    op.create_table(
        'vos_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('base_url', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('api_user', sa.String(length=128), nullable=True),
        sa.Column('api_password', sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vos_instances_id'), 'vos_instances', ['id'], unique=False)
    
    # Create phones table
    op.create_table(
        'phones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('e164', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=64), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('vos_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_phones_id'), 'phones', ['id'], unique=False)
    op.create_index(op.f('ix_phones_e164'), 'phones', ['e164'], unique=False)
    op.create_index(op.f('ix_phones_vos_id'), 'phones', ['vos_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_phones_vos_id'), table_name='phones')
    op.drop_index(op.f('ix_phones_e164'), table_name='phones')
    op.drop_index(op.f('ix_phones_id'), table_name='phones')
    op.drop_table('phones')
    op.drop_index(op.f('ix_vos_instances_id'), table_name='vos_instances')
    op.drop_table('vos_instances')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

