"""create CDR statistics tables

Revision ID: 0013_create_cdr_statistics_tables
Revises: 0012_extend_gateways_fields
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0013_cdr_statistics'
down_revision = '0012_extend_gateways_fields'
branch_labels = None
depends_on = None


def upgrade():
    """创建CDR统计表"""
    
    # 1. VOS节点级别的话单统计表
    op.create_table(
        'vos_cdr_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vos_id', sa.Integer(), nullable=False, comment='VOS实例ID'),
        sa.Column('vos_uuid', postgresql.UUID(as_uuid=True), nullable=False, comment='VOS节点UUID'),
        sa.Column('statistic_date', sa.Date(), nullable=False, comment='统计日期'),
        sa.Column('period_type', sa.String(length=10), nullable=False, comment='统计周期：day, month, quarter, year'),
        
        # 费用统计
        sa.Column('total_fee', sa.Numeric(precision=15, scale=4), nullable=True, server_default='0', comment='总费用'),
        
        # 时长统计
        sa.Column('total_duration', sa.BigInteger(), nullable=True, server_default='0', comment='总通话时长（秒，大于0秒的通话）'),
        sa.Column('total_calls', sa.BigInteger(), nullable=True, server_default='0', comment='总通话记录数'),
        sa.Column('connected_calls', sa.BigInteger(), nullable=True, server_default='0', comment='接通通话数（hold_time > 0）'),
        
        # 接通率
        sa.Column('connection_rate', sa.Numeric(precision=5, scale=2), nullable=True, server_default='0', comment='接通率（百分比）'),
        
        # 元数据
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vos_id', 'vos_uuid', 'statistic_date', 'period_type', name='uq_vos_cdr_statistics')
    )
    
    # 创建索引
    op.create_index('idx_vos_cdr_statistics_vos_id', 'vos_cdr_statistics', ['vos_id'], unique=False)
    op.create_index('idx_vos_cdr_statistics_vos_uuid', 'vos_cdr_statistics', ['vos_uuid'], unique=False)
    op.create_index('idx_vos_cdr_statistics_date', 'vos_cdr_statistics', ['statistic_date'], unique=False)
    op.create_index('idx_vos_cdr_statistics_period', 'vos_cdr_statistics', ['period_type'], unique=False)
    op.create_index('idx_vos_cdr_statistics_composite', 'vos_cdr_statistics', ['vos_uuid', 'statistic_date', 'period_type'], unique=False)
    
    # 2. 账户级别的话单统计表
    op.create_table(
        'account_cdr_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vos_id', sa.Integer(), nullable=False),
        sa.Column('vos_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_name', sa.String(length=256), nullable=False, comment='账户名称'),
        sa.Column('statistic_date', sa.Date(), nullable=False),
        sa.Column('period_type', sa.String(length=10), nullable=False),
        
        # 费用统计
        sa.Column('total_fee', sa.Numeric(precision=15, scale=4), nullable=True, server_default='0'),
        
        # 时长统计
        sa.Column('total_duration', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('total_calls', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('connected_calls', sa.BigInteger(), nullable=True, server_default='0'),
        
        # 接通率
        sa.Column('connection_rate', sa.Numeric(precision=5, scale=2), nullable=True, server_default='0'),
        
        # 元数据
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vos_id', 'vos_uuid', 'account_name', 'statistic_date', 'period_type', name='uq_account_cdr_statistics')
    )
    
    # 创建索引
    op.create_index('idx_account_cdr_statistics_vos_id', 'account_cdr_statistics', ['vos_id'], unique=False)
    op.create_index('idx_account_cdr_statistics_vos_uuid', 'account_cdr_statistics', ['vos_uuid'], unique=False)
    op.create_index('idx_account_cdr_statistics_account', 'account_cdr_statistics', ['account_name'], unique=False)
    op.create_index('idx_account_cdr_statistics_date', 'account_cdr_statistics', ['statistic_date'], unique=False)
    op.create_index('idx_account_cdr_statistics_composite', 'account_cdr_statistics', ['vos_uuid', 'account_name', 'statistic_date', 'period_type'], unique=False)
    
    # 3. 网关级别的话单统计表
    op.create_table(
        'gateway_cdr_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vos_id', sa.Integer(), nullable=False),
        sa.Column('vos_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('callee_gateway', sa.String(length=256), nullable=False, comment='落地网关'),
        sa.Column('statistic_date', sa.Date(), nullable=False),
        sa.Column('period_type', sa.String(length=10), nullable=False),
        
        # 费用统计
        sa.Column('total_fee', sa.Numeric(precision=15, scale=4), nullable=True, server_default='0'),
        
        # 时长统计
        sa.Column('total_duration', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('total_calls', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('connected_calls', sa.BigInteger(), nullable=True, server_default='0'),
        
        # 接通率
        sa.Column('connection_rate', sa.Numeric(precision=5, scale=2), nullable=True, server_default='0'),
        
        # 元数据
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vos_id', 'vos_uuid', 'callee_gateway', 'statistic_date', 'period_type', name='uq_gateway_cdr_statistics')
    )
    
    # 创建索引
    op.create_index('idx_gateway_cdr_statistics_vos_id', 'gateway_cdr_statistics', ['vos_id'], unique=False)
    op.create_index('idx_gateway_cdr_statistics_vos_uuid', 'gateway_cdr_statistics', ['vos_uuid'], unique=False)
    op.create_index('idx_gateway_cdr_statistics_gateway', 'gateway_cdr_statistics', ['callee_gateway'], unique=False)
    op.create_index('idx_gateway_cdr_statistics_date', 'gateway_cdr_statistics', ['statistic_date'], unique=False)
    op.create_index('idx_gateway_cdr_statistics_composite', 'gateway_cdr_statistics', ['vos_uuid', 'callee_gateway', 'statistic_date', 'period_type'], unique=False)


def downgrade():
    """删除CDR统计表"""
    # 删除索引
    op.drop_index('idx_gateway_cdr_statistics_composite', table_name='gateway_cdr_statistics')
    op.drop_index('idx_gateway_cdr_statistics_date', table_name='gateway_cdr_statistics')
    op.drop_index('idx_gateway_cdr_statistics_gateway', table_name='gateway_cdr_statistics')
    op.drop_index('idx_gateway_cdr_statistics_vos_uuid', table_name='gateway_cdr_statistics')
    op.drop_index('idx_gateway_cdr_statistics_vos_id', table_name='gateway_cdr_statistics')
    
    op.drop_index('idx_account_cdr_statistics_composite', table_name='account_cdr_statistics')
    op.drop_index('idx_account_cdr_statistics_date', table_name='account_cdr_statistics')
    op.drop_index('idx_account_cdr_statistics_account', table_name='account_cdr_statistics')
    op.drop_index('idx_account_cdr_statistics_vos_uuid', table_name='account_cdr_statistics')
    op.drop_index('idx_account_cdr_statistics_vos_id', table_name='account_cdr_statistics')
    
    op.drop_index('idx_vos_cdr_statistics_composite', table_name='vos_cdr_statistics')
    op.drop_index('idx_vos_cdr_statistics_period', table_name='vos_cdr_statistics')
    op.drop_index('idx_vos_cdr_statistics_date', table_name='vos_cdr_statistics')
    op.drop_index('idx_vos_cdr_statistics_vos_uuid', table_name='vos_cdr_statistics')
    op.drop_index('idx_vos_cdr_statistics_vos_id', table_name='vos_cdr_statistics')
    
    # 删除表
    op.drop_table('gateway_cdr_statistics')
    op.drop_table('account_cdr_statistics')
    op.drop_table('vos_cdr_statistics')
