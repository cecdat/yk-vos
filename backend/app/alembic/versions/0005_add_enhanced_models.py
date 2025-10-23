"""add enhanced models: gateway, phone_enhanced, fee_rate_group, suite

Revision ID: 0005_add_enhanced_models
Revises: 0004_add_vos_data_cache
Create Date: 2025-10-23 12:00:00.000001

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0005_add_enhanced_models'
down_revision = '0004_add_vos_data_cache'
branch_labels = None
depends_on = None

def upgrade():
    # 创建 gateways 表
    op.create_table(
        'gateways',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vos_instance_id', sa.Integer(), nullable=False),
        sa.Column('gateway_name', sa.String(length=255), nullable=False),
        sa.Column('gateway_type', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=100), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('protocol', sa.String(length=50), nullable=True),
        sa.Column('is_online', sa.Boolean(), nullable=True),
        sa.Column('asr', sa.Float(), nullable=True),
        sa.Column('acd', sa.Float(), nullable=True),
        sa.Column('concurrent_calls', sa.Integer(), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vos_instance_id'], ['vos_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建 gateways 索引
    op.create_index('ix_gateways_id', 'gateways', ['id'], unique=False)
    op.create_index('ix_gateways_vos_instance_id', 'gateways', ['vos_instance_id'], unique=False)
    op.create_index('ix_gateways_gateway_name', 'gateways', ['gateway_name'], unique=False)
    op.create_index('ix_gateways_gateway_type', 'gateways', ['gateway_type'], unique=False)
    op.create_index('ix_gateways_is_online', 'gateways', ['is_online'], unique=False)
    op.create_index('idx_gateway_vos_name', 'gateways', ['vos_instance_id', 'gateway_name'], unique=True)
    op.create_index('idx_gateway_online', 'gateways', ['vos_instance_id', 'is_online'], unique=False)
    op.create_index('idx_gateway_type', 'gateways', ['vos_instance_id', 'gateway_type'], unique=False)
    
    # 创建 phones_enhanced 表
    op.create_table(
        'phones_enhanced',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vos_instance_id', sa.Integer(), nullable=False),
        sa.Column('e164', sa.String(length=64), nullable=False),
        sa.Column('account', sa.String(length=255), nullable=True),
        sa.Column('is_online', sa.Boolean(), nullable=True),
        sa.Column('register_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address', sa.String(length=100), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('total_calls', sa.Integer(), nullable=True),
        sa.Column('total_duration', sa.Integer(), nullable=True),
        sa.Column('last_call_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('balance', sa.Float(), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vos_instance_id'], ['vos_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建 phones_enhanced 索引
    op.create_index('ix_phones_enhanced_id', 'phones_enhanced', ['id'], unique=False)
    op.create_index('ix_phones_enhanced_vos_instance_id', 'phones_enhanced', ['vos_instance_id'], unique=False)
    op.create_index('ix_phones_enhanced_e164', 'phones_enhanced', ['e164'], unique=False)
    op.create_index('ix_phones_enhanced_account', 'phones_enhanced', ['account'], unique=False)
    op.create_index('ix_phones_enhanced_is_online', 'phones_enhanced', ['is_online'], unique=False)
    op.create_index('idx_phone_vos_e164', 'phones_enhanced', ['vos_instance_id', 'e164'], unique=True)
    op.create_index('idx_phone_account', 'phones_enhanced', ['vos_instance_id', 'account'], unique=False)
    op.create_index('idx_phone_online', 'phones_enhanced', ['vos_instance_id', 'is_online'], unique=False)
    
    # 创建 fee_rate_groups 表
    op.create_table(
        'fee_rate_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vos_instance_id', sa.Integer(), nullable=False),
        sa.Column('group_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vos_instance_id'], ['vos_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建 fee_rate_groups 索引
    op.create_index('ix_fee_rate_groups_id', 'fee_rate_groups', ['id'], unique=False)
    op.create_index('ix_fee_rate_groups_vos_instance_id', 'fee_rate_groups', ['vos_instance_id'], unique=False)
    op.create_index('ix_fee_rate_groups_group_name', 'fee_rate_groups', ['group_name'], unique=False)
    op.create_index('idx_feerate_vos_name', 'fee_rate_groups', ['vos_instance_id', 'group_name'], unique=True)
    
    # 创建 suites 表
    op.create_table(
        'suites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vos_instance_id', sa.Integer(), nullable=False),
        sa.Column('suite_id', sa.String(length=100), nullable=False),
        sa.Column('suite_name', sa.String(length=255), nullable=True),
        sa.Column('suite_type', sa.String(length=100), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('monthly_fee', sa.Float(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['vos_instance_id'], ['vos_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建 suites 索引
    op.create_index('ix_suites_id', 'suites', ['id'], unique=False)
    op.create_index('ix_suites_vos_instance_id', 'suites', ['vos_instance_id'], unique=False)
    op.create_index('ix_suites_suite_id', 'suites', ['suite_id'], unique=False)
    op.create_index('idx_suite_vos_id', 'suites', ['vos_instance_id', 'suite_id'], unique=True)

def downgrade():
    # 删除 suites 表
    op.drop_index('idx_suite_vos_id', table_name='suites')
    op.drop_index('ix_suites_suite_id', table_name='suites')
    op.drop_index('ix_suites_vos_instance_id', table_name='suites')
    op.drop_index('ix_suites_id', table_name='suites')
    op.drop_table('suites')
    
    # 删除 fee_rate_groups 表
    op.drop_index('idx_feerate_vos_name', table_name='fee_rate_groups')
    op.drop_index('ix_fee_rate_groups_group_name', table_name='fee_rate_groups')
    op.drop_index('ix_fee_rate_groups_vos_instance_id', table_name='fee_rate_groups')
    op.drop_index('ix_fee_rate_groups_id', table_name='fee_rate_groups')
    op.drop_table('fee_rate_groups')
    
    # 删除 phones_enhanced 表
    op.drop_index('idx_phone_online', table_name='phones_enhanced')
    op.drop_index('idx_phone_account', table_name='phones_enhanced')
    op.drop_index('idx_phone_vos_e164', table_name='phones_enhanced')
    op.drop_index('ix_phones_enhanced_is_online', table_name='phones_enhanced')
    op.drop_index('ix_phones_enhanced_account', table_name='phones_enhanced')
    op.drop_index('ix_phones_enhanced_e164', table_name='phones_enhanced')
    op.drop_index('ix_phones_enhanced_vos_instance_id', table_name='phones_enhanced')
    op.drop_index('ix_phones_enhanced_id', table_name='phones_enhanced')
    op.drop_table('phones_enhanced')
    
    # 删除 gateways 表
    op.drop_index('idx_gateway_type', table_name='gateways')
    op.drop_index('idx_gateway_online', table_name='gateways')
    op.drop_index('idx_gateway_vos_name', table_name='gateways')
    op.drop_index('ix_gateways_is_online', table_name='gateways')
    op.drop_index('ix_gateways_gateway_type', table_name='gateways')
    op.drop_index('ix_gateways_gateway_name', table_name='gateways')
    op.drop_index('ix_gateways_vos_instance_id', table_name='gateways')
    op.drop_index('ix_gateways_id', table_name='gateways')
    op.drop_table('gateways')

