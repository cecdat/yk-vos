# 数据存储说明

## 📁 数据目录结构

```
yk-vos/
├── data/                          # 所有数据存储根目录
│   ├── clickhouse/                # ClickHouse 数据目录
│   │   ├── data/                  # 实际数据文件
│   │   ├── metadata/              # 元数据
│   │   ├── format_schemas/        # 格式定义
│   │   └── access/                # 访问控制
│   └── postgres/                  # PostgreSQL 数据目录
│       ├── base/                  # 数据库文件
│       ├── global/                # 全局对象
│       └── pg_wal/                # WAL 日志
├── clickhouse/
│   └── init/                      # ClickHouse 初始化脚本
│       └── 01_create_tables.sql   # 建表脚本
└── docker-compose.clickhouse.yaml # Docker Compose 配置
```

## 🗂️ 数据映射配置

### ClickHouse

```yaml
clickhouse:
  volumes:
    - ./data/clickhouse:/var/lib/clickhouse     # 数据映射
    - ./clickhouse/init:/docker-entrypoint-initdb.d  # 初始化脚本
```

**说明**：
- **宿主机路径**：`./data/clickhouse`
- **容器内路径**：`/var/lib/clickhouse`
- **UID/GID**：101:101
- **存储内容**：
  - 话单数据（cdrs 表）
  - 物化视图
  - 索引文件
  - 元数据

### PostgreSQL

```yaml
postgres:
  volumes:
    - ./data/postgres:/var/lib/postgresql/data  # 数据映射
```

**说明**：
- **宿主机路径**：`./data/postgres`
- **容器内路径**：`/var/lib/postgresql/data`
- **UID/GID**：999:999
- **存储内容**：
  - 用户账户
  - VOS 实例配置
  - 客户信息
  - 话机信息
  - 系统配置

## 💾 数据持久化

### 优点

1. **数据安全**：容器删除不影响数据
2. **易于备份**：直接备份 `data/` 目录
3. **快速恢复**：解压备份到 `data/` 即可
4. **性能好**：无额外的卷管理开销

### 注意事项

1. **权限问题**：
   - Linux 系统需要正确设置目录权限
   - ClickHouse: `chown -R 101:101 data/clickhouse`
   - PostgreSQL: `chown -R 999:999 data/postgres`

2. **磁盘空间**：
   - ClickHouse 建议至少 100GB（话单数据）
   - PostgreSQL 建议至少 20GB（配置数据）
   - 定期监控磁盘使用情况

3. **备份策略**：
   - 建议每天备份
   - 保留最近 7 天的备份
   - 重要数据异地备份

## 📊 数据量预估

### ClickHouse（话单数据）

| 话单量 | 未压缩 | 压缩后 | 推荐磁盘 |
|--------|--------|--------|----------|
| 100万 | 2GB | 200MB | 10GB |
| 1000万 | 20GB | 2GB | 50GB |
| 1亿 | 200GB | 20GB | 100GB |
| 10亿 | 2TB | 200GB | 500GB |

**压缩比**：约 10:1

### PostgreSQL（配置数据）

| 数据类型 | 数量 | 存储空间 |
|----------|------|----------|
| 用户 | 100 | < 1MB |
| VOS实例 | 50 | < 1MB |
| 客户 | 10万 | ~50MB |
| 话机 | 10万 | ~50MB |
| 配置 | - | ~10MB |

**总计**：通常 < 1GB

## 🔄 备份和恢复

### 方法 1：目录备份（推荐）

```bash
# 备份
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz data/

# 恢复
tar -xzf backup-20251024-103000.tar.gz
```

### 方法 2：ClickHouse 原生备份

```bash
# 备份（在容器内）
docker-compose exec clickhouse clickhouse-client --query "BACKUP TABLE vos_cdrs.cdrs TO Disk('default', 'backups/cdrs_20251024')"

# 恢复
docker-compose exec clickhouse clickhouse-client --query "RESTORE TABLE vos_cdrs.cdrs FROM Disk('default', 'backups/cdrs_20251024')"
```

### 方法 3：PostgreSQL 原生备份

```bash
# 备份
docker-compose exec postgres pg_dump -U vos_user vosadmin > backup_pg_$(date +%Y%m%d).sql

# 恢复
docker-compose exec -T postgres psql -U vos_user vosadmin < backup_pg_20251024.sql
```

## 🗑️ 数据清理策略

### ClickHouse 自动分区删除

```sql
-- 删除 12 个月前的分区（按月分区）
ALTER TABLE cdrs DROP PARTITION '202210';
```

### 定时清理脚本

创建 `cleanup-old-data.sh`：

```bash
#!/bin/bash

# 保留最近 12 个月的数据
CUTOFF_DATE=$(date -d "12 months ago" +%Y%m)

# 获取所有分区
docker-compose exec clickhouse clickhouse-client --query "
SELECT DISTINCT partition 
FROM system.parts 
WHERE database = 'vos_cdrs' AND table = 'cdrs' AND partition < '$CUTOFF_DATE'
" | while read partition; do
    echo "删除分区: $partition"
    docker-compose exec clickhouse clickhouse-client --query "
    ALTER TABLE vos_cdrs.cdrs DROP PARTITION '$partition'
    "
done

echo "数据清理完成"
```

## 📈 监控和维护

### 查看存储使用情况

```bash
# ClickHouse 数据量
docker-compose exec clickhouse clickhouse-client --query "
SELECT 
    table,
    formatReadableSize(sum(bytes)) as size,
    count() as parts,
    sum(rows) as rows
FROM system.parts
WHERE database = 'vos_cdrs' AND active
GROUP BY table
"

# PostgreSQL 数据量
docker-compose exec postgres psql -U vos_user -d vosadmin -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# 宿主机磁盘使用
du -sh data/clickhouse data/postgres
```

### 性能优化

```sql
-- ClickHouse 表优化（合并分区）
OPTIMIZE TABLE vos_cdrs.cdrs FINAL;

-- PostgreSQL 表优化
VACUUM ANALYZE;
```

## 🔒 数据安全建议

1. **定期备份**：
   - 每天备份一次
   - 保留最近 7-30 天
   - 异地备份重要数据

2. **访问控制**：
   - 限制数据目录访问权限
   - 定期更换数据库密码
   - 使用防火墙限制端口访问

3. **灾难恢复**：
   - 准备恢复脚本
   - 定期测试恢复流程
   - 记录恢复时间（RTO）

4. **监控告警**：
   - 磁盘使用率 > 80% 告警
   - 备份失败告警
   - 数据库连接异常告警

## 📝 迁移和扩容

### 迁移到新服务器

```bash
# 1. 在旧服务器上打包
tar -czf yk-vos-data-backup.tar.gz data/

# 2. 传输到新服务器
scp yk-vos-data-backup.tar.gz user@new-server:/data/yk-vos/

# 3. 在新服务器上解压
cd /data/yk-vos
tar -xzf yk-vos-data-backup.tar.gz

# 4. 设置权限
sudo chown -R 101:101 data/clickhouse
sudo chown -R 999:999 data/postgres

# 5. 启动服务
docker-compose -f docker-compose.clickhouse.yaml up -d
```

### 扩容磁盘

如果数据目录所在磁盘空间不足：

```bash
# 1. 停止服务
docker-compose down

# 2. 挂载新磁盘到 /mnt/new-disk

# 3. 移动数据
sudo mv data/clickhouse /mnt/new-disk/
sudo mv data/postgres /mnt/new-disk/

# 4. 创建软链接
ln -s /mnt/new-disk/clickhouse data/clickhouse
ln -s /mnt/new-disk/postgres data/postgres

# 5. 启动服务
docker-compose -f docker-compose.clickhouse.yaml up -d
```

## 🎯 最佳实践

1. **数据目录独立磁盘**：
   - 将 `data/` 挂载到独立磁盘
   - 使用 SSD 提升性能
   - 预留足够空间（至少 2 倍预估量）

2. **定期维护**：
   - 每周检查磁盘空间
   - 每月优化数据库
   - 每季度清理旧数据

3. **监控指标**：
   - 磁盘使用率
   - 数据增长速率
   - 查询响应时间
   - 备份成功率


