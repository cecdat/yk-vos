#!/usr/bin/env python3
"""
填充ClickHouse中缺失的vos_uuid字段
执行时间: 2025-01
说明: 根据PostgreSQL中的vos_instances表，为ClickHouse中vos_uuid为空的记录填充UUID
"""
import sys
import os

# 添加项目根目录到路径（容器内工作目录是/srv，app在/srv/app）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.clickhouse_db import get_clickhouse_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fill_clickhouse_vos_uuid():
    """
    填充ClickHouse中缺失的vos_uuid
    """
    # 从环境变量读取数据库配置
    postgres_user = os.getenv('POSTGRES_USER', 'vosadmin')
    postgres_password = os.getenv('POSTGRES_PASSWORD', 'Ykxx@2025')
    postgres_db = os.getenv('POSTGRES_DB', 'vosadmin')
    postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    
    # 从DATABASE_URL环境变量解析（如果存在）
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        database_url = f'postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}'
    
    try:
        # 连接PostgreSQL
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        # 获取所有VOS实例的ID和UUID映射
        result = db.execute(text("""
            SELECT id, vos_uuid::text as vos_uuid_str
            FROM vos_instances
            WHERE vos_uuid IS NOT NULL
        """))
        
        vos_uuid_map = {}
        for row in result:
            vos_uuid_map[row.id] = row.vos_uuid_str
        
        if not vos_uuid_map:
            logger.warning("PostgreSQL中没有找到VOS实例UUID，跳过填充")
            return
        
        logger.info(f"从PostgreSQL获取到 {len(vos_uuid_map)} 个VOS实例的UUID映射")
        
        # 连接ClickHouse
        ch_db = get_clickhouse_db()
        
        # 检查cdrs表是否存在
        try:
            result = ch_db.execute("SELECT count() FROM cdrs LIMIT 1")
            logger.info("ClickHouse cdrs表存在")
        except Exception as e:
            logger.warning(f"ClickHouse cdrs表不存在或无法访问: {e}")
            return
        
        # 统计需要填充的记录数
        total_empty = 0
        for vos_id, vos_uuid in vos_uuid_map.items():
            count_query = f"SELECT count() FROM cdrs WHERE vos_id = {vos_id} AND (vos_uuid = '' OR vos_uuid IS NULL)"
            try:
                result = ch_db.execute(count_query)
                empty_count = result[0][0] if result else 0
                if empty_count > 0:
                    total_empty += empty_count
                    logger.info(f"  VOS ID {vos_id}: 发现 {empty_count} 条记录需要填充UUID")
            except Exception as e:
                logger.warning(f"  查询VOS ID {vos_id}的记录数失败: {e}")
        
        if total_empty == 0:
            logger.info("ClickHouse中所有记录的vos_uuid都已填充，无需操作")
            return
        
        logger.info(f"总共需要填充 {total_empty} 条记录的vos_uuid")
        
        # 分批填充（每次处理一个VOS实例）
        # 注意：ClickHouse的ALTER TABLE UPDATE是异步操作
        import time
        total_updated = 0
        
        for vos_id, vos_uuid in vos_uuid_map.items():
            try:
                # 检查是否有需要更新的记录
                count_query = f"SELECT count() FROM cdrs WHERE vos_id = {vos_id} AND (vos_uuid = '' OR vos_uuid IS NULL)"
                result = ch_db.execute(count_query)
                empty_count = result[0][0] if result else 0
                
                if empty_count == 0:
                    logger.info(f"  VOS ID {vos_id}: 无需更新")
                    continue
                
                logger.info(f"  VOS ID {vos_id}: 开始更新 {empty_count} 条记录...")
                
                # 执行异步UPDATE操作
                # 注意：ClickHouse的ALTER TABLE UPDATE是异步的，需要等待合并完成
                update_query = f"""
                    ALTER TABLE cdrs 
                    UPDATE vos_uuid = '{vos_uuid}' 
                    WHERE vos_id = {vos_id} AND (vos_uuid = '' OR vos_uuid IS NULL)
                """
                
                # 执行UPDATE（这会返回一个异步操作ID）
                ch_db.execute(update_query)
                
                # 等待异步操作完成（ClickHouse需要时间合并）
                logger.info(f"  VOS ID {vos_id}: UPDATE操作已提交，等待后台合并...")
                
                # 等待一段时间让合并执行
                time.sleep(2)
                
                # 查询更新后的记录数
                verify_query = f"SELECT count() FROM cdrs WHERE vos_id = {vos_id} AND vos_uuid = '{vos_uuid}'"
                result = ch_db.execute(verify_query)
                updated_count = result[0][0] if result else 0
                
                logger.info(f"  ✅ VOS ID {vos_id}: UUID已设置为 {vos_uuid}，当前匹配 {updated_count} 条记录")
                total_updated += empty_count
                
            except Exception as e:
                logger.error(f"  ❌ VOS ID {vos_id}: 更新失败: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"✅ ClickHouse UUID填充操作已提交，预计将更新 {total_updated} 条记录")
        logger.info("   注意：ClickHouse的UPDATE是异步操作，实际合并可能需要一些时间")
        
    except Exception as e:
        logger.error(f"❌ UUID填充失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == '__main__':
    fill_clickhouse_vos_uuid()

