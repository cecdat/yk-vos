"""create app_configs table

Revision ID: 0015_create_app_configs
Revises: 0014_dashboard_stats
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = '0015_app_configs'
down_revision = '0014_dashboard_stats'
branch_labels = None
depends_on = None


def upgrade():
    """创建应用配置表"""
    op.create_table(
        'app_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_key', sa.String(length=100), nullable=False, comment='配置键'),
        sa.Column('config_value', sa.String(length=500), nullable=True, comment='配置值'),
        sa.Column('description', sa.String(length=500), nullable=True, comment='配置描述'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_app_configs_config_key', 'app_configs', ['config_key'], unique=True)
    op.create_index('ix_app_configs_id', 'app_configs', ['id'], unique=False)
    
    # 插入默认配置（使用 PostgreSQL 的 ON CONFLICT 语法）
    op.execute("""
        INSERT INTO app_configs (config_key, config_value, description)
        VALUES 
            ('cdr_sync_time', '01:30', 'CDR同步时间（HH:MM格式）'),
            ('customer_sync_time', '01:00', '客户数据同步时间（HH:MM格式）'),
            ('cdr_sync_days', '1', 'CDR同步天数（1-30天）')
        ON CONFLICT (config_key) DO NOTHING
    """)


def downgrade():
    """删除应用配置表"""
    op.drop_index('ix_app_configs_id', table_name='app_configs')
    op.drop_index('ix_app_configs_config_key', table_name='app_configs')
    op.drop_table('app_configs')

