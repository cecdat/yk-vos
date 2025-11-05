"""create dashboard statistics views

Revision ID: 0014_create_dashboard_statistics_views
Revises: 0013_create_cdr_statistics_tables
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0014_dashboard_stats'
down_revision = '0013_cdr_statistics'
branch_labels = None
depends_on = None


def upgrade():
    """创建仪表盘统计视图"""
    
    # 1. 客户统计视图（按实例汇总）
    op.execute("""
        CREATE OR REPLACE VIEW vw_customer_statistics AS
        SELECT 
            vi.id AS instance_id,
            vi.name AS instance_name,
            vi.vos_uuid,
            vi.enabled AS instance_enabled,
            COUNT(c.id) AS total_customers,
            COUNT(CASE WHEN c.is_in_debt = TRUE THEN 1 END) AS debt_customers,
            COALESCE(SUM(CASE WHEN c.is_in_debt = TRUE THEN 1 ELSE 0 END), 0) AS debt_count
        FROM vos_instances vi
        LEFT JOIN customers c ON c.vos_instance_id = vi.id
        WHERE vi.enabled = TRUE
        GROUP BY vi.id, vi.name, vi.vos_uuid, vi.enabled;
    """)
    
    # 2. 实例健康状态视图
    op.execute("""
        CREATE OR REPLACE VIEW vw_instance_health_summary AS
        SELECT 
            vi.id AS instance_id,
            vi.name AS instance_name,
            vi.vos_uuid,
            vi.enabled,
            vi.base_url,
            vi.description,
            COALESCE(vhc.status, 'unknown') AS health_status,
            vhc.last_check_at AS health_last_check,
            vhc.response_time_ms AS health_response_time,
            vhc.consecutive_failures,
            vhc.error_message AS health_error
        FROM vos_instances vi
        LEFT JOIN vos_health_checks vhc ON vhc.vos_instance_id = vi.id
        ORDER BY vi.id;
    """)
    
    # 3. 仪表盘统计物化视图（汇总所有统计数据）
    # 物化视图可以提高查询性能，但需要定期刷新
    op.execute("""
        CREATE MATERIALIZED VIEW mv_dashboard_statistics AS
        SELECT 
            vi.id AS instance_id,
            vi.name AS instance_name,
            vi.vos_uuid,
            vi.enabled,
            
            -- 客户统计
            COALESCE(vcs.total_customers, 0) AS total_customers,
            COALESCE(vcs.debt_customers, 0) AS debt_customers,
            
            -- 健康状态
            COALESCE(vhs.health_status, 'unknown') AS health_status,
            vhs.health_last_check,
            vhs.health_response_time
            
        FROM vos_instances vi
        LEFT JOIN vw_customer_statistics vcs ON vcs.instance_id = vi.id
        LEFT JOIN vw_instance_health_summary vhs ON vhs.instance_id = vi.id
        WHERE vi.enabled = TRUE;
    """)
    
    # 为物化视图创建索引（提高查询性能）
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_dashboard_statistics_instance_id 
        ON mv_dashboard_statistics (instance_id);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_mv_dashboard_statistics_enabled 
        ON mv_dashboard_statistics (enabled);
    """)
    
    # 创建刷新物化视图的函数（可以在后台任务中调用）
    op.execute("""
        CREATE OR REPLACE FUNCTION refresh_dashboard_statistics()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_statistics;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade():
    """删除视图和物化视图"""
    op.execute("DROP FUNCTION IF EXISTS refresh_dashboard_statistics() CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_statistics CASCADE;")
    op.execute("DROP VIEW IF EXISTS vw_instance_health_summary CASCADE;")
    op.execute("DROP VIEW IF EXISTS vw_customer_statistics CASCADE;")
