"""recreate cdrs table with TimescaleDB

Revision ID: 0009_recreate_cdrs_with_timescaledb
Revises: 0008_add_sync_configs
Create Date: 2025-10-23

此迁移将：
1. 备份现有的cdrs表数据
2. 删除旧的cdrs表
3. 创建新的cdrs表（使用新字段结构）
4. 转换为TimescaleDB超表（按时间自动分区）
5. 设置自动压缩和数据保留策略
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '0009_recreate_cdrs_with_timescaledb'
down_revision = '0008_add_sync_configs'
branch_labels = None
depends_on = None


def upgrade():
    """升级：创建TimescaleDB超表"""
    
    # 1. 备份现有数据（如果表存在）
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cdrs') THEN
                -- 创建备份表
                CREATE TABLE IF NOT EXISTS cdrs_backup_20251023 AS SELECT * FROM cdrs;
                
                -- 删除旧表
                DROP TABLE cdrs CASCADE;
                
                RAISE NOTICE '已备份现有cdrs表数据到 cdrs_backup_20251023';
            END IF;
        END $$;
    """)
    
    # 2. 创建新的cdrs表（使用复合主键以满足TimescaleDB要求）
    op.create_table(
        'cdrs',
        # 基础字段
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='自增ID（非主键，用于排序和引用）'),
        sa.Column('vos_id', sa.Integer(), nullable=False, comment='VOS实例ID'),
        
        # 账户信息
        sa.Column('account_name', sa.String(length=128), nullable=True, comment='账户名称'),
        sa.Column('account', sa.String(length=64), nullable=True, comment='账户号码'),
        
        # 呼叫信息
        sa.Column('caller_e164', sa.String(length=64), nullable=True, comment='主叫号码'),
        sa.Column('callee_access_e164', sa.String(length=64), nullable=True, comment='被叫号码'),
        
        # 时间信息（TimescaleDB分区键 + 主键之一）
        sa.Column('start', sa.DateTime(), nullable=False, comment='起始时间（主键之一）'),
        sa.Column('stop', sa.DateTime(), nullable=True, comment='终止时间'),
        
        # 时长和费用
        sa.Column('hold_time', sa.Integer(), nullable=True, comment='通话时长(秒)'),
        sa.Column('fee_time', sa.Integer(), nullable=True, comment='计费时长(秒)'),
        sa.Column('fee', sa.Numeric(precision=10, scale=4), nullable=True, comment='通话费用'),
        
        # 终止信息
        sa.Column('end_reason', sa.String(length=128), nullable=True, comment='终止原因'),
        sa.Column('end_direction', sa.SmallInteger(), nullable=True, comment='挂断方(0主叫，1被叫，2服务器)'),
        
        # 网关和IP
        sa.Column('callee_gateway', sa.String(length=64), nullable=True, comment='主叫经由路由'),
        sa.Column('callee_ip', sa.String(length=64), nullable=True, comment='被叫IP地址'),
        
        # 原始数据和唯一标识
        sa.Column('raw', JSONB, nullable=True, comment='原始话单数据(JSONB格式)'),
        sa.Column('flow_no', sa.String(length=64), nullable=False, comment='话单唯一标识（主键之一）'),
        
        # 复合主键（满足TimescaleDB要求：包含分区列start）
        sa.PrimaryKeyConstraint('start', 'flow_no'),
        
        comment='VOS话单记录表（TimescaleDB超表）'
    )
    
    # 3. 安装TimescaleDB扩展（如果未安装）
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
    
    # 4. 转换为TimescaleDB超表（按start字段分区）
    # ⚠️ 必须在创建任何唯一索引之前创建 hypertable
    op.execute("""
        SELECT create_hypertable(
            'cdrs', 
            'start',
            chunk_time_interval => INTERVAL '7 days',  -- 每7天一个分区
            if_not_exists => TRUE
        );
    """)
    
    # 5. 创建索引（必须在 hypertable 创建之后）
    # 注意：start和flow_no已是主键，自动有索引
    op.create_index('ix_cdrs_vos_id', 'cdrs', ['vos_id'], unique=False)
    op.create_index('ix_cdrs_account', 'cdrs', ['account'], unique=False)
    op.create_index('ix_cdrs_caller_e164', 'cdrs', ['caller_e164'], unique=False)
    op.create_index('ix_cdrs_callee_access_e164', 'cdrs', ['callee_access_e164'], unique=False)
    op.create_index('ix_cdrs_callee_gateway', 'cdrs', ['callee_gateway'], unique=False)
    
    # 创建复合索引（优化常见查询）
    op.create_index('idx_cdrs_vos_start', 'cdrs', ['vos_id', 'start'], unique=False)
    op.create_index('idx_cdrs_account_start', 'cdrs', ['account', 'start'], unique=False)
    
    # id字段的索引（非唯一，因为TimescaleDB不允许不包含分区列的唯一索引）
    # 如果需要通过id查询，这个索引足够了
    op.create_index('ix_cdrs_id', 'cdrs', ['id'], unique=False)
    
    # 6. 设置压缩策略（30天后自动压缩）
    op.execute("""
        ALTER TABLE cdrs SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'vos_id',
            timescaledb.compress_orderby = 'start DESC, flow_no'
        );
    """)
    
    op.execute("""
        SELECT add_compression_policy('cdrs', INTERVAL '30 days');
    """)
    
    # 7. 设置数据保留策略（自动删除1年前的数据）
    op.execute("""
        SELECT add_retention_policy('cdrs', INTERVAL '1 year');
    """)
    
    # 8. 创建连续聚合视图（可选，用于快速统计）
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS cdrs_hourly_stats
        WITH (timescaledb.continuous) AS
        SELECT 
            time_bucket('1 hour', start) AS hour,
            vos_id,
            account,
            COUNT(*) as call_count,
            SUM(hold_time) as total_hold_time,
            SUM(fee) as total_fee,
            AVG(hold_time) as avg_hold_time
        FROM cdrs
        GROUP BY hour, vos_id, account
        WITH NO DATA;
    """)
    
    # 9. 为连续聚合视图添加刷新策略
    op.execute("""
        SELECT add_continuous_aggregate_policy('cdrs_hourly_stats',
            start_offset => INTERVAL '3 hours',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour');
    """)
    
    print("✅ TimescaleDB超表创建成功！")
    print("📊 已启用：")
    print("  - 自动分区（每7天一个chunk）")
    print("  - 自动压缩（30天后压缩，压缩比约10:1）")
    print("  - 自动删除（1年后自动删除）")
    print("  - 连续聚合（每小时统计）")


def downgrade():
    """降级：恢复原始表结构"""
    
    # 删除连续聚合视图
    op.execute("DROP MATERIALIZED VIEW IF EXISTS cdrs_hourly_stats CASCADE;")
    
    # 删除TimescaleDB超表
    op.execute("DROP TABLE IF EXISTS cdrs CASCADE;")
    
    # 恢复备份数据（如果存在）
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cdrs_backup_20251023') THEN
                -- 恢复备份表
                ALTER TABLE cdrs_backup_20251023 RENAME TO cdrs;
                RAISE NOTICE '已从备份恢复cdrs表';
            END IF;
        END $$;
    """)

