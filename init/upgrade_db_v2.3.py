#!/usr/bin/env python3
"""
VOS节点唯一UUID迁移脚本
用于升级现有数据库，添加VOS节点的唯一UUID支持
"""

import os
import sys
import uuid
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.db import engine
from backend.app.models.vos_instance import VOSInstance
from backend.app.models.vos_data_cache import VosDataCache
from backend.app.models.gateway import Gateway
from backend.app.models.customer import Customer
from backend.app.models.cdr import CDR
from backend.app.models.phone import Phone
from backend.app.models.vos_health import VOSHealthCheck
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

def run_migration():
    """执行数据库迁移"""
    print("开始执行VOS节点唯一UUID迁移...")
    
    # 创建数据库会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. 检查vos_instances表是否已有vos_uuid字段
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'vos_instances' 
            AND column_name = 'vos_uuid'
        """))
        
        has_uuid_column = result.fetchone() is not None
        
        if not has_uuid_column:
            print("添加vos_uuid字段到vos_instances表...")
            db.execute(text("ALTER TABLE vos_instances ADD COLUMN vos_uuid UUID"))
            db.commit()
        
        # 2. 为现有VOS实例生成UUID
        print("为现有VOS实例生成UUID...")
        instances = db.query(VOSInstance).filter(VOSInstance.vos_uuid.is_(None)).all()
        
        for instance in instances:
            instance.vos_uuid = uuid.uuid4()
            print(f"  为VOS实例 '{instance.name}' (ID: {instance.id}) 生成UUID: {instance.vos_uuid}")
        
        db.commit()
        
        # 3. 为相关表添加vos_uuid字段并填充数据
        tables_to_update = [
            ('vos_data_cache', 'vos_instance_id'),
            ('gateways', 'vos_instance_id'),
            ('customers', 'vos_instance_id'),
            ('cdrs', 'vos_id'),
            ('phones', 'vos_id'),
            ('vos_health_check', 'vos_instance_id')
        ]
        
        for table_name, id_column in tables_to_update:
            print(f"更新表 {table_name}...")
            
            # 检查是否已有vos_uuid字段
            result = db.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND column_name = 'vos_uuid'
            """))
            
            if result.fetchone() is None:
                print(f"  添加vos_uuid字段到 {table_name} 表...")
                db.execute(text(f"ALTER TABLE {table_name} ADD COLUMN vos_uuid UUID"))
                db.commit()
            
            # 填充vos_uuid数据
            if id_column == 'vos_id':
                # 对于cdrs和phones表，使用vos_id字段
                db.execute(text(f"""
                    UPDATE {table_name} 
                    SET vos_uuid = vi.vos_uuid 
                    FROM vos_instances vi 
                    WHERE {table_name}.{id_column} = vi.id 
                    AND {table_name}.vos_uuid IS NULL
                """))
            else:
                # 对于其他表，使用vos_instance_id字段
                db.execute(text(f"""
                    UPDATE {table_name} 
                    SET vos_uuid = vi.vos_uuid 
                    FROM vos_instances vi 
                    WHERE {table_name}.{id_column} = vi.id 
                    AND {table_name}.vos_uuid IS NULL
                """))
            
            db.commit()
            print(f"  {table_name} 表更新完成")
        
        # 4. 添加索引
        print("添加索引...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_vos_instances_uuid ON vos_instances(vos_uuid)",
            "CREATE INDEX IF NOT EXISTS idx_vos_data_cache_uuid ON vos_data_cache(vos_uuid)",
            "CREATE INDEX IF NOT EXISTS idx_gateways_uuid ON gateways(vos_uuid)",
            "CREATE INDEX IF NOT EXISTS idx_customers_uuid ON customers(vos_uuid)",
            "CREATE INDEX IF NOT EXISTS idx_cdrs_uuid ON cdrs(vos_uuid)",
            "CREATE INDEX IF NOT EXISTS idx_phones_uuid ON phones(vos_uuid)",
            "CREATE INDEX IF NOT EXISTS idx_vos_health_check_uuid ON vos_health_check(vos_uuid)"
        ]
        
        for index_sql in indexes:
            db.execute(text(index_sql))
        
        db.commit()
        
        # 5. 更新数据库版本
        print("更新数据库版本...")
        db.execute(text("""
            INSERT INTO db_versions (version, description, applied_at) 
            VALUES ('2.3', '添加VOS节点唯一UUID支持，支持IP变更时数据关联不中断', NOW())
            ON CONFLICT (version) DO UPDATE SET 
                description = EXCLUDED.description,
                applied_at = EXCLUDED.applied_at
        """))
        db.commit()
        
        print("✅ VOS节点唯一UUID迁移完成！")
        
        # 6. 显示迁移结果
        print("\n迁移结果统计:")
        result = db.execute(text("SELECT COUNT(*) FROM vos_instances"))
        instance_count = result.scalar()
        print(f"  VOS实例数量: {instance_count}")
        
        for table_name in ['vos_data_cache', 'gateways', 'customers', 'cdrs', 'phones', 'vos_health_check']:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE vos_uuid IS NOT NULL"))
            count = result.scalar()
            print(f"  {table_name} 表已更新记录数: {count}")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
