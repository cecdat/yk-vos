# ClickHouse 架构迁移方案

## 📋 概述

**目标**：将数据库从 PostgreSQL + TimescaleDB 迁移到 ClickHouse

**优势**：
- ✅ 更适合海量话单数据（亿级）
- ✅ 更好的列式存储和压缩（节省80%空间）
- ✅ 更快的分析查询（10-100倍提升）
- ✅ 天然支持时间分区
- ✅ 更简单的扩展性

## 📐 架构对比

### 原架构（PostgreSQL + TimescaleDB）
```
services:
  - postgres (TimescaleDB)  → 存储所有数据
  - redis                   → 缓存
  - backend                 → FastAPI
  - celery-worker/beat      → 后台任务
```

### 新架构（ClickHouse）
```
services:
  - clickhouse             → 存储话单数据（CDR）⭐新增
  - postgres               → 存储配置数据（用户、VOS实例等）
  - redis                  → 缓存
  - backend                → FastAPI
  - celery-worker/beat     → 后台任务
```

## 🗂️ 数据分配策略

### ClickHouse（OLAP - 分析型）
- ✅ CDR 话单数据（海量、时序、不更新）
- ✅ 统计报表数据
- ✅ 日志数据

### PostgreSQL（OLTP - 事务型）
- ✅ 用户账户信息
- ✅ VOS 实例配置
- ✅ 客户信息
- ✅ 话机信息
- ✅ 同步配置
- ✅ 健康检查记录

## 🔧 实施步骤

### 步骤 1：更新 docker-compose.yaml

### 步骤 2：创建 ClickHouse 连接配置

### 步骤 3：重构 CDR 模型

### 步骤 4：更新数据访问层

### 步骤 5：数据迁移（如果需要）

### 步骤 6：测试验证

## 📦 具体实现

详细的配置文件和代码修改见：
- `docker-compose.clickhouse.yaml`
- `backend/app/core/clickhouse_db.py`
- `backend/app/models/clickhouse/cdr.py`
- `MIGRATION_GUIDE.md`

## ⚠️ 注意事项

1. **ClickHouse特性**：
   - 不支持事务
   - 删除/更新操作昂贵
   - 适合追加写入场景

2. **数据一致性**：
   - CDR数据只写入一次
   - 使用 ReplacingMergeTree 去重

3. **查询优化**：
   - 尽量使用时间范围过滤
   - 避免 SELECT *
   - 利用分区键

## 🚀 部署方案

### 全新部署（推荐）
```bash
# 使用新的 docker-compose 配置
docker-compose -f docker-compose.clickhouse.yaml up -d
```

### 平滑迁移
1. 并行运行 PostgreSQL 和 ClickHouse
2. 双写一段时间
3. 验证数据完整性
4. 切换读取
5. 停止 PostgreSQL CDR 写入

## 📊 性能对比

### 查询速度
- 百万级话单查询：从 2-5秒 → 100-300ms
- 千万级话单查询：从 30秒+ → 1-3秒
- 聚合统计：提升 10-100倍

### 存储空间
- 压缩比：约 10:1
- 1亿条话单：从 200GB → 20GB

### 写入性能
- 批量写入：从 10K/s → 100K+/s

## 🎯 迁移时间线

- **准备阶段**：1-2天（配置、测试）
- **实施阶段**：半天（部署、验证）
- **优化阶段**：1周（监控、调优）

## 🔍 回滚方案

如果出现问题，可以快速回滚到 PostgreSQL：
1. 停止新系统
2. 启动原 docker-compose.yaml
3. 数据仍在 `./data/postgres` 目录


