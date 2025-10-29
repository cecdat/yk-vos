#!/usr/bin/env python3
"""
填充已有VOS节点的UUID到数据库中
执行时间: 2025-01
说明: 为所有未设置UUID的VOS节点生成并填充UUID
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fill_vos_uuid():
    """
    填充已有VOS节点的UUID
    """
    # 从环境变量读取数据库配置
    postgres_user = os.getenv('POSTGRES_USER', 'vos_user')
    postgres_password = os.getenv('POSTGRES_PASSWORD', 'vos_password')
    postgres_db = os.getenv('POSTGRES_DB', 'vosadmin')
    postgres_host = os.getenv('POSTGRES_HOST', 'postgres')  # Docker环境下使用服务名
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    
    database_url = f'postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}'
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        # 检查vos_instances表是否存在
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'vos_instances'
            )
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            logger.warning("vos_instances表不存在，跳过UUID填充")
            return
        
        # 检查是否有vos_uuid列
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'vos_instances' AND column_name = 'vos_uuid'
            )
        """))
        column_exists = result.scalar()
        
        if not column_exists:
            logger.warning("vos_instances表没有vos_uuid列，跳过UUID填充")
            return
        
        # 统计需要填充的记录数
        result = db.execute(text("""
            SELECT COUNT(*) FROM vos_instances WHERE vos_uuid IS NULL
        """))
        count = result.scalar()
        
        if count == 0:
            logger.info("所有VOS节点已经有UUID，无需填充")
            return
        
        logger.info(f"找到 {count} 个未设置UUID的VOS节点，开始填充...")
        
        # 为每个节点生成UUID
        result = db.execute(text("""
            UPDATE vos_instances 
            SET vos_uuid = gen_random_uuid() 
            WHERE vos_uuid IS NULL
            RETURNING id, name
        """))
        updated_records = result.fetchall()
        
        # 提交更改
        db.commit()
        
        logger.info(f"✅ 成功为 {len(updated_records)} 个VOS节点生成UUID:")
        for record in updated_records:
            logger.info(f"  - ID {record[0]}: {record[1]}")
        
        # 填充所有相关数据的vos_uuid
        logger.info("开始填充相关数据的vos_uuid...")
        
        # 填充vos_data_cache
        result = db.execute(text("""
            UPDATE vos_data_cache 
            SET vos_uuid = vi.vos_uuid 
            FROM vos_instances vi 
            WHERE vos_data_cache.vos_instance_id = vi.id 
            AND vos_data_cache.vos_uuid IS NULL
        """))
        logger.info(f"  ✅ vos_data_cache: 更新了 {result.rowcount} 条记录")
        
        # 填充gateways
        result = db.execute(text("""
            UPDATE gateways 
            SET vos_uuid = vi.vos_uuid 
            FROM vos_instances vi 
            WHERE gateways.vos_instance_id = vi.id 
            AND gateways.vos_uuid IS NULL
        """))
        logger.info(f"  ✅ gateways: 更新了 {result.rowcount} 条记录")
        
        # 填充customers
        result = db.execute(text("""
            UPDATE customers 
            SET vos_uuid = vi.vos_uuid 
            FROM vos_instances vi 
            WHERE customers.vos_instance_id = vi.id 
            AND customers.vos_uuid IS NULL
        """))
        logger.info(f"  ✅ customers: 更新了 {result.rowcount} 条记录")
        
        # 填充cdrs (PostgreSQL)
        result = db.execute(text("""
            UPDATE cdrs 
            SET vos_uuid = vi.vos_uuid 
            FROM vos_instances vi 
            WHERE cdrs.vos_id = vi.id 
            AND cdrs.vos_uuid IS NULL
        """))
        logger.info(f"  ✅ cdrs: 更新了 {result.rowcount} 条记录")
        
        # 填充phones
        result = db.execute(text("""
            UPDATE phones 
            SET vos_uuid = vi.vos_uuid 
            FROM vos_instances vi 
            WHERE phones.vos_id = vi.id 
            AND phones.vos_uuid IS NULL
        """))
        logger.info(f"  ✅ phones: 更新了 {result.rowcount} 条记录")
        
        # 填充vos_health_check (支持两种表名)
        for table_name in ['vos_health_check', 'vos_health_checks']:
            result = db.execute(text(f"""
                UPDATE {table_name} 
                SET vos_uuid = vi.vos_uuid 
                FROM vos_instances vi 
                WHERE {table_name}.vos_instance_id = vi.id 
                AND {table_name}.vos_uuid IS NULL
            """))
            if result.rowcount > 0:
                logger.info(f"  ✅ {table_name}: 更新了 {result.rowcount} 条记录")
                break
        
        db.commit()
        logger.info("✅ UUID填充完成")
        
    except Exception as e:
        logger.error(f"❌ UUID填充失败: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    fill_vos_uuid()

