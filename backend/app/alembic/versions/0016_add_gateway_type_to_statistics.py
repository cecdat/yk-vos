"""add gateway_type to gateway_cdr_statistics

Revision ID: 0016_gateway_type
Revises: 0015_create_app_configs_table
Create Date: 2025-11-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0016_gateway_type'
down_revision = '0015_app_configs'  # 注意：这里应该匹配 0015_create_app_configs_table.py 中的 revision ID
branch_labels = None
depends_on = None


def upgrade():
    # 1. 添加新字段
    op.add_column('gateway_cdr_statistics', sa.Column('gateway_name', sa.String(length=256), nullable=True, comment='网关名称'))
    op.add_column('gateway_cdr_statistics', sa.Column('gateway_type', sa.String(length=20), nullable=True, comment='网关类型：caller（对接网关）或callee（落地网关）'))
    
    # 2. 将callee_gateway的数据迁移到gateway_name，并设置gateway_type为'callee'
    op.execute("""
        UPDATE gateway_cdr_statistics 
        SET gateway_name = callee_gateway,
            gateway_type = 'callee'
        WHERE gateway_name IS NULL
    """)
    
    # 3. 设置新字段为NOT NULL
    op.alter_column('gateway_cdr_statistics', 'gateway_name', nullable=False)
    op.alter_column('gateway_cdr_statistics', 'gateway_type', nullable=False)
    
    # 4. 删除旧字段callee_gateway
    op.drop_column('gateway_cdr_statistics', 'callee_gateway')
    
    # 5. 删除旧的唯一约束和索引
    op.drop_constraint('uq_gateway_cdr_statistics', 'gateway_cdr_statistics', type_='unique')
    op.drop_index('idx_gateway_cdr_statistics_composite', table_name='gateway_cdr_statistics')
    
    # 6. 创建新的唯一约束和索引
    op.create_unique_constraint(
        'uq_gateway_cdr_statistics',
        'gateway_cdr_statistics',
        ['vos_id', 'vos_uuid', 'gateway_name', 'gateway_type', 'statistic_date', 'period_type']
    )
    op.create_index(
        'idx_gateway_cdr_statistics_composite',
        'gateway_cdr_statistics',
        ['vos_uuid', 'gateway_name', 'gateway_type', 'statistic_date', 'period_type']
    )


def downgrade():
    # 1. 删除新的唯一约束和索引
    op.drop_index('idx_gateway_cdr_statistics_composite', table_name='gateway_cdr_statistics')
    op.drop_constraint('uq_gateway_cdr_statistics', 'gateway_cdr_statistics', type_='unique')
    
    # 2. 添加回callee_gateway字段
    op.add_column('gateway_cdr_statistics', sa.Column('callee_gateway', sa.String(length=256), nullable=True))
    
    # 3. 将gateway_name的数据迁移回callee_gateway（只迁移gateway_type='callee'的数据）
    op.execute("""
        UPDATE gateway_cdr_statistics 
        SET callee_gateway = gateway_name
        WHERE gateway_type = 'callee' AND callee_gateway IS NULL
    """)
    
    # 4. 设置callee_gateway为NOT NULL
    op.alter_column('gateway_cdr_statistics', 'callee_gateway', nullable=False)
    
    # 5. 删除新字段
    op.drop_column('gateway_cdr_statistics', 'gateway_type')
    op.drop_column('gateway_cdr_statistics', 'gateway_name')
    
    # 6. 恢复旧的唯一约束和索引
    op.create_unique_constraint(
        'uq_gateway_cdr_statistics',
        'gateway_cdr_statistics',
        ['vos_id', 'vos_uuid', 'callee_gateway', 'statistic_date', 'period_type']
    )
    op.create_index(
        'idx_gateway_cdr_statistics_composite',
        'gateway_cdr_statistics',
        ['vos_uuid', 'callee_gateway', 'statistic_date', 'period_type']
    )

