"""add vos_data_cache table for generic VOS API data caching

Revision ID: 0004_add_vos_data_cache
Revises: 0003_add_cdr_hash
Create Date: 2025-10-23 00:00:00.000001

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0004_add_vos_data_cache'
down_revision = '0003_add_cdr_hash'
branch_labels = None
depends_on = None

def upgrade():
    # 创建 vos_data_cache 表
    op.create_table(
        'vos_data_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vos_instance_id', sa.Integer(), nullable=False),
        sa.Column('api_path', sa.String(length=255), nullable=False),
        sa.Column('api_name', sa.String(length=128), nullable=True),
        sa.Column('cache_key', sa.String(length=255), nullable=False),
        sa.Column('query_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=True),
        sa.Column('ret_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vos_instance_id'], ['vos_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_vos_data_cache_id', 'vos_data_cache', ['id'], unique=False)
    op.create_index('ix_vos_data_cache_vos_instance_id', 'vos_data_cache', ['vos_instance_id'], unique=False)
    op.create_index('ix_vos_data_cache_api_path', 'vos_data_cache', ['api_path'], unique=False)
    op.create_index('ix_vos_data_cache_cache_key', 'vos_data_cache', ['cache_key'], unique=False)
    op.create_index('ix_vos_data_cache_is_valid', 'vos_data_cache', ['is_valid'], unique=False)
    op.create_index('ix_vos_data_cache_synced_at', 'vos_data_cache', ['synced_at'], unique=False)
    op.create_index('ix_vos_data_cache_expires_at', 'vos_data_cache', ['expires_at'], unique=False)
    
    # 创建复合索引
    op.create_index('idx_vos_api_cache', 'vos_data_cache', ['vos_instance_id', 'api_path', 'cache_key'], unique=True)
    op.create_index('idx_vos_cache_valid', 'vos_data_cache', ['vos_instance_id', 'is_valid', 'expires_at'], unique=False)
    op.create_index('idx_vos_cache_expires', 'vos_data_cache', ['expires_at'], unique=False)

def downgrade():
    # 删除索引
    op.drop_index('idx_vos_cache_expires', table_name='vos_data_cache')
    op.drop_index('idx_vos_cache_valid', table_name='vos_data_cache')
    op.drop_index('idx_vos_api_cache', table_name='vos_data_cache')
    op.drop_index('ix_vos_data_cache_expires_at', table_name='vos_data_cache')
    op.drop_index('ix_vos_data_cache_synced_at', table_name='vos_data_cache')
    op.drop_index('ix_vos_data_cache_is_valid', table_name='vos_data_cache')
    op.drop_index('ix_vos_data_cache_cache_key', table_name='vos_data_cache')
    op.drop_index('ix_vos_data_cache_api_path', table_name='vos_data_cache')
    op.drop_index('ix_vos_data_cache_vos_instance_id', table_name='vos_data_cache')
    op.drop_index('ix_vos_data_cache_id', table_name='vos_data_cache')
    
    # 删除表
    op.drop_table('vos_data_cache')

