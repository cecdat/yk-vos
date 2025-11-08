"""create account detail reports view

Revision ID: 0018_account_detail_reports_view
Revises: 0017_account_detail_reports
Create Date: 2025-11-06 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0018_account_detail_reports_view'
down_revision = '0017_account_detail_reports'
branch_labels = None
depends_on = None


def upgrade():
    """创建账户明细报表查询视图"""
    
    # 账户明细报表视图（包含VOS实例信息，便于查询）
    op.execute("""
        CREATE OR REPLACE VIEW vw_account_detail_reports AS
        SELECT 
            adr.id,
            adr.vos_instance_id,
            vi.name AS instance_name,
            adr.vos_uuid,
            adr.account,
            adr.account_name,
            -- 将UTC时间戳（毫秒）转换为日期时间
            to_timestamp(adr.begin_time / 1000.0) AT TIME ZONE 'UTC' AS begin_datetime,
            to_timestamp(adr.end_time / 1000.0) AT TIME ZONE 'UTC' AS end_datetime,
            -- 提取日期部分
            date(to_timestamp(adr.begin_time / 1000.0) AT TIME ZONE 'UTC') AS report_date,
            adr.begin_time,
            adr.end_time,
            adr.cdr_count,
            adr.total_fee,
            adr.total_time,
            adr.total_suite_fee,
            adr.total_suite_fee_time,
            adr.net_fee,
            adr.net_time,
            adr.net_count,
            adr.local_fee,
            adr.local_time,
            adr.local_count,
            adr.domestic_fee,
            adr.domestic_time,
            adr.domestic_count,
            adr.international_fee,
            adr.international_time,
            adr.international_count,
            adr.created_at,
            adr.updated_at
        FROM account_detail_reports adr
        LEFT JOIN vos_instances vi ON vi.id = adr.vos_instance_id
        ORDER BY adr.vos_instance_id, adr.account, adr.begin_time DESC;
    """)


def downgrade():
    """删除账户明细报表视图"""
    op.execute("DROP VIEW IF EXISTS vw_account_detail_reports;")

