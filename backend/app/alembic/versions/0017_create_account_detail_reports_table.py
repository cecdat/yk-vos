"""create account detail reports table

Revision ID: 0017_account_detail_reports
Revises: 0016_add_gateway_type_to_statistics
Create Date: 2025-11-06 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = '0017_account_detail_reports'
down_revision = '0016_add_gateway_type_to_statistics'
branch_labels = None
depends_on = None


def upgrade():
    # 创建账户明细报表表
    op.create_table(
        'account_detail_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vos_instance_id', sa.Integer(), nullable=False, comment='VOS实例ID'),
        sa.Column('vos_uuid', postgresql.UUID(as_uuid=True), nullable=False, comment='VOS节点UUID'),
        sa.Column('account', sa.String(length=255), nullable=False, comment='账户号码'),
        sa.Column('account_name', sa.String(length=255), nullable=True, comment='账户名称'),
        sa.Column('begin_time', sa.BigInteger(), nullable=False, comment='起始时间（UTC 1970-01-01 至今的毫秒数）'),
        sa.Column('end_time', sa.BigInteger(), nullable=False, comment='终止时间（UTC 1970-01-01 至今的毫秒数）'),
        sa.Column('cdr_count', sa.BigInteger(), nullable=True, server_default='0', comment='话单总计'),
        sa.Column('total_fee', sa.Numeric(precision=15, scale=4), nullable=True, server_default='0', comment='费用总计'),
        sa.Column('total_time', sa.BigInteger(), nullable=True, server_default='0', comment='计费时长总计（秒）'),
        sa.Column('total_suite_fee', sa.Numeric(precision=15, scale=4), nullable=True, server_default='0', comment='套餐费用总计'),
        sa.Column('total_suite_fee_time', sa.BigInteger(), nullable=True, server_default='0', comment='套餐费用时长'),
        sa.Column('net_fee', sa.Numeric(precision=15, scale=4), nullable=True, server_default='0', comment='网络费用'),
        sa.Column('net_time', sa.BigInteger(), nullable=True, server_default='0', comment='网络时长'),
        sa.Column('net_count', sa.BigInteger(), nullable=True, server_default='0', comment='网络数量'),
        sa.Column('local_fee', sa.Numeric(precision=15, scale=4), nullable=True, server_default='0', comment='本地费用'),
        sa.Column('local_time', sa.BigInteger(), nullable=True, server_default='0', comment='本地时长'),
        sa.Column('local_count', sa.BigInteger(), nullable=True, server_default='0', comment='本地数量'),
        sa.Column('domestic_fee', sa.Numeric(precision=15, scale=4), nullable=True, server_default='0', comment='国内通话费用'),
        sa.Column('domestic_time', sa.BigInteger(), nullable=True, server_default='0', comment='国内通话计费时长（秒）'),
        sa.Column('domestic_count', sa.BigInteger(), nullable=True, server_default='0', comment='国内通话数量'),
        sa.Column('international_fee', sa.Numeric(precision=15, scale=4), nullable=True, server_default='0', comment='国际费用'),
        sa.Column('international_time', sa.BigInteger(), nullable=True, server_default='0', comment='国际时长'),
        sa.Column('international_count', sa.BigInteger(), nullable=True, server_default='0', comment='国际数量'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['vos_instance_id'], ['vos_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_account_detail_reports_id', 'account_detail_reports', ['id'], unique=False)
    op.create_index('ix_account_detail_reports_vos_instance_id', 'account_detail_reports', ['vos_instance_id'], unique=False)
    op.create_index('ix_account_detail_reports_vos_uuid', 'account_detail_reports', ['vos_uuid'], unique=False)
    op.create_index('ix_account_detail_reports_account', 'account_detail_reports', ['account'], unique=False)
    op.create_index('ix_account_detail_reports_begin_time', 'account_detail_reports', ['begin_time'], unique=False)
    op.create_index('ix_account_detail_reports_end_time', 'account_detail_reports', ['end_time'], unique=False)
    
    # 创建复合索引
    op.create_index('idx_account_detail_report_vos_account', 'account_detail_reports', 
                    ['vos_instance_id', 'vos_uuid', 'account'], unique=False)
    op.create_index('idx_account_detail_report_time', 'account_detail_reports', 
                    ['begin_time', 'end_time'], unique=False)
    op.create_index('idx_account_detail_report_account_time', 'account_detail_reports', 
                    ['account', 'begin_time', 'end_time'], unique=False)
    
    # 创建唯一约束
    op.create_unique_constraint('uq_account_detail_report', 'account_detail_reports', 
                                ['vos_instance_id', 'vos_uuid', 'account', 'begin_time', 'end_time'])


def downgrade():
    # 删除唯一约束
    op.drop_constraint('uq_account_detail_report', 'account_detail_reports', type_='unique')
    
    # 删除索引
    op.drop_index('idx_account_detail_report_account_time', table_name='account_detail_reports')
    op.drop_index('idx_account_detail_report_time', table_name='account_detail_reports')
    op.drop_index('idx_account_detail_report_vos_account', table_name='account_detail_reports')
    op.drop_index('ix_account_detail_reports_end_time', table_name='account_detail_reports')
    op.drop_index('ix_account_detail_reports_begin_time', table_name='account_detail_reports')
    op.drop_index('ix_account_detail_reports_account', table_name='account_detail_reports')
    op.drop_index('ix_account_detail_reports_vos_uuid', table_name='account_detail_reports')
    op.drop_index('ix_account_detail_reports_vos_instance_id', table_name='account_detail_reports')
    op.drop_index('ix_account_detail_reports_id', table_name='account_detail_reports')
    
    # 删除表
    op.drop_table('account_detail_reports')

