"""add sync_configs table

Revision ID: 0008_add_sync_configs
Revises: 0007_add_customers_table
Create Date: 2025-10-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = '0008_add_sync_configs'
down_revision = '0007_add_customers_table'
branch_labels = None
depends_on = None


def upgrade():
    """创建同步配置表"""
    op.create_table(
        'sync_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='配置名称'),
        sa.Column('description', sa.String(length=500), nullable=True, comment='配置描述'),
        sa.Column('cron_expression', sa.String(length=100), nullable=False, comment='Cron表达式'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true', comment='是否启用'),
        sa.Column('sync_type', sa.String(length=50), nullable=False, comment='同步类型'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_sync_configs_name', 'sync_configs', ['name'], unique=True)
    op.create_index('ix_sync_configs_id', 'sync_configs', ['id'], unique=False)
    
    # 插入默认配置
    op.execute("""
        INSERT INTO sync_configs (name, description, cron_expression, enabled, sync_type)
        VALUES 
            ('客户数据同步', '每10分钟同步一次客户数据', '*/10 * * * *', true, 'customers'),
            ('话机状态同步', '每5分钟同步一次话机在线状态', '*/5 * * * *', true, 'phones'),
            ('话单数据同步', '每天凌晨1:30同步前一天的话单', '30 1 * * *', true, 'cdrs')
    """)


def downgrade():
    """删除同步配置表"""
    op.drop_index('ix_sync_configs_id', table_name='sync_configs')
    op.drop_index('ix_sync_configs_name', table_name='sync_configs')
    op.drop_table('sync_configs')

