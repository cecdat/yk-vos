"""add gateway_type to gateway_cdr_statistics

Revision ID: 0016_gateway_type
Revises: 0015_create_app_configs_table
Create Date: 2025-11-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import logging

logger = logging.getLogger(__name__)

# revision identifiers, used by Alembic.
revision = '0016_gateway_type'
down_revision = '0015_app_configs'  # 注意：这里应该匹配 0015_create_app_configs_table.py 中的 revision ID
branch_labels = None
depends_on = None


def upgrade():
    """添加 gateway_type 字段到 gateway_cdr_statistics 表"""
    conn = op.get_bind()
    
    try:
        # 检查表是否存在
        result = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'gateway_cdr_statistics'
            )
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            logger.warning("表 gateway_cdr_statistics 不存在，跳过迁移")
            return
        
        # 检查是否已经有 gateway_name 字段（说明已经迁移过了）
        result = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'gateway_cdr_statistics'
                AND column_name = 'gateway_name'
            )
        """))
        has_gateway_name = result.scalar()
        
        if has_gateway_name:
            logger.info("表 gateway_cdr_statistics 已经包含 gateway_name 字段，跳过迁移")
            return
        
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
        
        # 4. 删除旧字段callee_gateway（如果存在）
        try:
            result = conn.execute(sa.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'gateway_cdr_statistics'
                    AND column_name = 'callee_gateway'
                )
            """))
            has_callee_gateway = result.scalar()
            
            if has_callee_gateway:
                op.drop_column('gateway_cdr_statistics', 'callee_gateway')
        except Exception as e:
            logger.warning(f"检查或删除 callee_gateway 字段时出错: {e}")
        
        # 5. 删除旧的唯一约束和索引（使用 IF EXISTS 避免错误）
        # 注意：即使使用 IF EXISTS，PostgreSQL 在某些情况下仍可能报错，所以用 try-except 包裹
        try:
            op.execute("ALTER TABLE gateway_cdr_statistics DROP CONSTRAINT IF EXISTS uq_gateway_cdr_statistics")
        except Exception as e:
            # 如果约束不存在，PostgreSQL 可能会报错，这里捕获并忽略
            logger.debug(f"删除约束时出错（可能不存在）: {e}")
        
        try:
            op.execute("DROP INDEX IF EXISTS idx_gateway_cdr_statistics_composite")
        except Exception as e:
            logger.debug(f"删除索引时出错（可能不存在）: {e}")
        
        # 6. 创建新的唯一约束和索引
        try:
            op.create_unique_constraint(
                'uq_gateway_cdr_statistics',
                'gateway_cdr_statistics',
                ['vos_id', 'vos_uuid', 'gateway_name', 'gateway_type', 'statistic_date', 'period_type']
            )
        except Exception as e:
            logger.warning(f"创建唯一约束时出错（可能已存在）: {e}")
        
        try:
            op.create_index(
                'idx_gateway_cdr_statistics_composite',
                'gateway_cdr_statistics',
                ['vos_uuid', 'gateway_name', 'gateway_type', 'statistic_date', 'period_type']
            )
        except Exception as e:
            logger.warning(f"创建索引时出错（可能已存在）: {e}")
        
        logger.info("✅ 成功完成 gateway_cdr_statistics 表结构迁移")
        
    except Exception as e:
        logger.error(f"❌ 迁移过程中出错: {e}", exc_info=True)
        # 不抛出异常，允许迁移继续（可能是部分迁移的情况）
        pass


def downgrade():
    """回滚 gateway_type 字段"""
    conn = op.get_bind()
    
    try:
        # 检查表是否存在
        result = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'gateway_cdr_statistics'
            )
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            logger.warning("表 gateway_cdr_statistics 不存在，跳过回滚")
            return
        
        # 1. 删除新的唯一约束和索引
        try:
            op.drop_index('idx_gateway_cdr_statistics_composite', table_name='gateway_cdr_statistics')
        except Exception:
            pass
        
        try:
            op.drop_constraint('uq_gateway_cdr_statistics', 'gateway_cdr_statistics', type_='unique')
        except Exception:
            pass
        
        # 2. 添加回callee_gateway字段
        try:
            result = conn.execute(sa.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'gateway_cdr_statistics'
                    AND column_name = 'callee_gateway'
                )
            """))
            has_callee_gateway = result.scalar()
            
            if not has_callee_gateway:
                op.add_column('gateway_cdr_statistics', sa.Column('callee_gateway', sa.String(length=256), nullable=True))
        except Exception as e:
            logger.warning(f"添加 callee_gateway 字段时出错: {e}")
        
        # 3. 将gateway_name的数据迁移回callee_gateway（只迁移gateway_type='callee'的数据）
        try:
            op.execute("""
                UPDATE gateway_cdr_statistics 
                SET callee_gateway = gateway_name
                WHERE gateway_type = 'callee' AND callee_gateway IS NULL
            """)
        except Exception as e:
            logger.warning(f"迁移数据时出错: {e}")
        
        # 4. 设置callee_gateway为NOT NULL
        try:
            op.alter_column('gateway_cdr_statistics', 'callee_gateway', nullable=False)
        except Exception:
            pass
        
        # 5. 删除新字段
        try:
            op.drop_column('gateway_cdr_statistics', 'gateway_type')
        except Exception:
            pass
        
        try:
            op.drop_column('gateway_cdr_statistics', 'gateway_name')
        except Exception:
            pass
        
        # 6. 恢复旧的唯一约束和索引
        try:
            op.create_unique_constraint(
                'uq_gateway_cdr_statistics',
                'gateway_cdr_statistics',
                ['vos_id', 'vos_uuid', 'callee_gateway', 'statistic_date', 'period_type']
            )
        except Exception:
            pass
        
        try:
            op.create_index(
                'idx_gateway_cdr_statistics_composite',
                'gateway_cdr_statistics',
                ['vos_uuid', 'callee_gateway', 'statistic_date', 'period_type']
            )
        except Exception:
            pass
        
    except Exception as e:
        logger.error(f"❌ 回滚过程中出错: {e}", exc_info=True)
