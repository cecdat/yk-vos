"""optimize CDR indexes

Revision ID: 0006
Revises: 0005
Create Date: 2025-10-23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None

def upgrade():
    # 为CDR表添加性能优化索引
    
    # 1. 复合索引：vos_id + start_time（用于按实例和时间范围查询）
    op.create_index(
        'idx_cdr_vos_time',
        'cdrs',
        ['vos_id', 'start_time'],
        unique=False
    )
    
    # 2. caller 索引（用于主叫号码查询）
    op.create_index(
        'idx_cdr_caller',
        'cdrs',
        ['caller'],
        unique=False
    )
    
    # 3. callee 索引（用于被叫号码查询）
    op.create_index(
        'idx_cdr_callee',
        'cdrs',
        ['callee'],
        unique=False
    )
    
    # 4. caller_gateway 索引（用于网关查询）
    op.create_index(
        'idx_cdr_caller_gateway',
        'cdrs',
        ['caller_gateway'],
        unique=False
    )
    
    # 5. callee_gateway 索引（用于网关查询）
    op.create_index(
        'idx_cdr_callee_gateway',
        'cdrs',
        ['callee_gateway'],
        unique=False
    )

def downgrade():
    # 删除索引
    op.drop_index('idx_cdr_callee_gateway', table_name='cdrs')
    op.drop_index('idx_cdr_caller_gateway', table_name='cdrs')
    op.drop_index('idx_cdr_callee', table_name='cdrs')
    op.drop_index('idx_cdr_caller', table_name='cdrs')
    op.drop_index('idx_cdr_vos_time', table_name='cdrs')

