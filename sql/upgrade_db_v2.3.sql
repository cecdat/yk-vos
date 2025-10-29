-- 升级数据库到 v2.3: 添加VOS节点唯一UUID支持
-- 执行时间: 2025-01-XX
-- 说明: 为VOS节点添加唯一UUID字段，支持IP变更时数据关联不中断

-- 检查是否已经执行过此升级
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'db_versions') THEN
        IF EXISTS (SELECT 1 FROM db_versions WHERE version = '2.3') THEN
            RAISE NOTICE '数据库已经是v2.3版本，跳过升级';
            RETURN;
        END IF;
    END IF;
END $$;

-- 1. 添加vos_uuid字段到vos_instances表
ALTER TABLE vos_instances 
ADD COLUMN IF NOT EXISTS vos_uuid UUID;

-- 2. 为现有记录生成UUID
UPDATE vos_instances 
SET vos_uuid = gen_random_uuid() 
WHERE vos_uuid IS NULL;

-- 3. 设置vos_uuid为NOT NULL并添加唯一约束
ALTER TABLE vos_instances 
ALTER COLUMN vos_uuid SET NOT NULL;

-- 4. 添加唯一约束（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE constraint_name = 'uq_vos_instances_uuid' 
                   AND table_name = 'vos_instances') THEN
        ALTER TABLE vos_instances ADD CONSTRAINT uq_vos_instances_uuid UNIQUE (vos_uuid);
    END IF;
END $$;

-- 5. 添加索引提高查询性能
CREATE INDEX IF NOT EXISTS idx_vos_instances_uuid ON vos_instances(vos_uuid);

-- 6. 为所有相关表添加vos_uuid字段（用于未来迁移）
-- 注意：这些字段暂时不设为外键，保持向后兼容

-- vos_data_cache表
ALTER TABLE vos_data_cache 
ADD COLUMN IF NOT EXISTS vos_uuid UUID;

-- gateways表  
ALTER TABLE gateways 
ADD COLUMN IF NOT EXISTS vos_uuid UUID;

-- customers表
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS vos_uuid UUID;

-- cdrs表
ALTER TABLE cdrs 
ADD COLUMN IF NOT EXISTS vos_uuid UUID;

-- phones表
ALTER TABLE phones 
ADD COLUMN IF NOT EXISTS vos_uuid UUID;

-- vos_health_check表（检查表名）
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vos_health_check') THEN
        ALTER TABLE vos_health_check ADD COLUMN IF NOT EXISTS vos_uuid UUID;
    ELSIF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vos_health_checks') THEN
        ALTER TABLE vos_health_checks ADD COLUMN IF NOT EXISTS vos_uuid UUID;
    END IF;
END $$;

-- 7. 为现有数据填充vos_uuid（基于vos_instance_id关联）
UPDATE vos_data_cache 
SET vos_uuid = vi.vos_uuid 
FROM vos_instances vi 
WHERE vos_data_cache.vos_instance_id = vi.id 
AND vos_data_cache.vos_uuid IS NULL;

UPDATE gateways 
SET vos_uuid = vi.vos_uuid 
FROM vos_instances vi 
WHERE gateways.vos_instance_id = vi.id 
AND gateways.vos_uuid IS NULL;

UPDATE customers 
SET vos_uuid = vi.vos_uuid 
FROM vos_instances vi 
WHERE customers.vos_instance_id = vi.id 
AND customers.vos_uuid IS NULL;

UPDATE cdrs 
SET vos_uuid = vi.vos_uuid 
FROM vos_instances vi 
WHERE cdrs.vos_id = vi.id 
AND cdrs.vos_uuid IS NULL;

UPDATE phones 
SET vos_uuid = vi.vos_uuid 
FROM vos_instances vi 
WHERE phones.vos_id = vi.id 
AND phones.vos_uuid IS NULL;

-- 更新vos_health_check表的vos_uuid（检查表名）
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vos_health_check') THEN
        UPDATE vos_health_check 
        SET vos_uuid = vi.vos_uuid 
        FROM vos_instances vi 
        WHERE vos_health_check.vos_instance_id = vi.id 
        AND vos_health_check.vos_uuid IS NULL;
    ELSIF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vos_health_checks') THEN
        UPDATE vos_health_checks 
        SET vos_uuid = vi.vos_uuid 
        FROM vos_instances vi 
        WHERE vos_health_checks.vos_instance_id = vi.id 
        AND vos_health_checks.vos_uuid IS NULL;
    END IF;
END $$;

-- 8. 添加索引提高查询性能（只对存在的表）
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vos_data_cache') THEN
        CREATE INDEX IF NOT EXISTS idx_vos_data_cache_uuid ON vos_data_cache(vos_uuid);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'gateways') THEN
        CREATE INDEX IF NOT EXISTS idx_gateways_uuid ON gateways(vos_uuid);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'customers') THEN
        CREATE INDEX IF NOT EXISTS idx_customers_uuid ON customers(vos_uuid);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cdrs') THEN
        CREATE INDEX IF NOT EXISTS idx_cdrs_uuid ON cdrs(vos_uuid);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'phones') THEN
        CREATE INDEX IF NOT EXISTS idx_phones_uuid ON phones(vos_uuid);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vos_health_check') THEN
        CREATE INDEX IF NOT EXISTS idx_vos_health_check_uuid ON vos_health_check(vos_uuid);
    ELSIF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vos_health_checks') THEN
        CREATE INDEX IF NOT EXISTS idx_vos_health_checks_uuid ON vos_health_checks(vos_uuid);
    END IF;
END $$;

-- 9. 更新数据库版本（如果表存在）
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'db_versions') THEN
        INSERT INTO db_versions (version, description, applied_at) 
        VALUES ('2.3', '添加VOS节点唯一UUID支持，支持IP变更时数据关联不中断', NOW())
        ON CONFLICT (version) DO UPDATE SET 
            description = EXCLUDED.description,
            applied_at = EXCLUDED.applied_at;
    END IF;
END $$;

-- 完成提示
SELECT 'VOS节点唯一UUID支持已添加完成' as status;
