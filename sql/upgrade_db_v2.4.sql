-- ====================================
-- 数据库升级脚本 v2.4
-- 功能：修复 cdrs 表缺少 account_name 字段
-- 执行时间：2025-10-30
-- ====================================

-- 版本检查：如果已应用则跳过
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM db_versions 
        WHERE version = '2.4' AND applied_at IS NOT NULL
    ) THEN
        RAISE NOTICE '版本 2.4 已应用，跳过执行';
        RETURN;
    END IF;
END $$;

-- 1. 为 cdrs 表添加 account_name 字段（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cdrs' 
        AND column_name = 'account_name'
    ) THEN
        ALTER TABLE cdrs ADD COLUMN account_name VARCHAR(128);
        COMMENT ON COLUMN cdrs.account_name IS '账户名称';
        RAISE NOTICE '已添加 cdrs.account_name 字段';
    ELSE
        RAISE NOTICE 'cdrs.account_name 字段已存在，跳过';
    END IF;
END $$;

-- 2. 记录版本信息
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'db_versions') THEN
        INSERT INTO db_versions (version, description, applied_at)
        VALUES ('2.4', 'CDR表添加account_name字段', NOW())
        ON CONFLICT (version) DO UPDATE 
        SET applied_at = NOW(), description = EXCLUDED.description;
        RAISE NOTICE '版本 2.4 已记录';
    ELSE
        RAISE NOTICE 'db_versions 表不存在，跳过版本记录';
    END IF;
END $$;

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'v2.4 升级完成：CDR表字段修复';
    RAISE NOTICE '========================================';
END $$;

