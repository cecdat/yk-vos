# YK-VOS - VOS3000 管理与分析平台

一个现代化的 VOS3000 管理和分析平台，提供实时监控、历史话单查询、智能数据分析和多维度统计功能。

## 📋 目录

- [核心特性](#核心特性)
- [技术栈](#技术栈)
- [系统架构](#系统架构)
- [数据流程](#数据流程)
- [统计计算公式](#统计计算公式)
- [快速开始](#快速开始)
- [部署指南](#部署指南)
- [项目结构](#项目结构)
- [API文档](#api文档)
- [故障排查](#故障排查)

## ✨ 核心特性

- 📊 **实时监控**: VOS实例健康状态、在线话机、网关状态实时监控
- 📞 **话单查询**: 历史CDR数据查询和导出（支持亿级数据）
- 👥 **客户管理**: 账户信息自动同步和管理
- 🔄 **智能缓存**: 三级缓存机制（Redis → PostgreSQL → VOS API）
- 📈 **多维度统计**: VOS节点/账户/网关三级统计，支持日/月/季度/年统计
- 🗄️ **双数据库架构**: PostgreSQL (配置) + ClickHouse (话单)
- 🐳 **容器化部署**: Docker Compose 一键部署
- ⏰ **自动同步**: Celery 定时任务自动同步VOS数据

## 🏗️ 技术栈

### 后端技术栈

- **Web框架**: FastAPI 0.104+ (Python 3.11+)
- **ORM框架**: SQLAlchemy 2.0+
- **关系数据库**: PostgreSQL 15 (存储配置数据和统计结果)
- **分析数据库**: ClickHouse (存储海量话单数据)
- **缓存**: Redis 7 (缓存VOS API响应)
- **异步任务**: Celery + Redis (后台任务队列)
- **数据库迁移**: Alembic

### 前端技术栈

- **框架**: Next.js 14 (React 18+)
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **图表**: Recharts
- **状态管理**: React Hooks + Context API

### 基础设施

- **容器化**: Docker + Docker Compose
- **Web服务器**: Uvicorn (ASGI)
- **进程管理**: Supervisord (容器内)

## 🏛️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Next.js)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Dashboard │  │  VOS管理 │  │ 话单查询 │  │ 统计分析 │   │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘   │
└────────┼──────────────┼─────────────┼─────────────┼────────┘
         │              │             │             │
         └──────────────┼─────────────┼─────────────┘
                        │             │
         ┌──────────────▼─────────────▼──────────────┐
         │         后端API层 (FastAPI)                │
         │  ┌─────────────────────────────────────┐  │
         │  │  认证授权  │  路由层  │  业务逻辑   │  │
         │  └──────────┬───────────────────┬──────┘  │
         └─────────────┼───────────────────┼─────────┘
                       │                   │
    ┌──────────────────┼───────────────────┼──────────────────┐
    │                  │                   │                  │
┌───▼────────┐  ┌──────▼───────┐  ┌───────▼──────┐  ┌──────▼──────┐
│ PostgreSQL │  │  ClickHouse  │  │    Redis     │  │   Celery    │
│ 配置+统计  │  │   话单数据    │  │   缓存队列   │  │  定时任务   │
└────────────┘  └──────────────┘  └──────────────┘  └─────────────┘
    │                  │
    └──────────┬───────┘
               │
    ┌──────────▼──────────┐
    │    VOS3000 API      │
    │   (外部VOS服务器)    │
    └─────────────────────┘
```

### 数据库架构

#### PostgreSQL (配置数据库)

**职责**: 存储系统配置、用户数据、统计结果

**核心表**:
- `users` - 用户账户表
- `vos_instances` - VOS实例配置表
- `vos_data_cache` - VOS API数据缓存表
- `customers` - 客户信息表
- `gateways` - 网关信息表
- `phones` - 话机信息表
- `cdr_statistics` - **统一统计表**（VOS/账户/网关三级统计）
- `db_versions` - 数据库版本管理表

#### ClickHouse (分析数据库)

**职责**: 存储海量话单数据，支持高速查询分析

**核心表**:
- `cdrs` - 话单记录表
  - 按月自动分区 (`PARTITION BY toYYYYMM(start)`)
  - 使用 `ReplacingMergeTree` 引擎自动去重
  - 索引优化：账户、主叫、被叫、网关

**物化视图**:
- `cdrs_daily_stats` - 按天统计（账户维度）
- `cdrs_account_stats` - 账户实时统计
- `cdrs_gateway_stats` - 网关统计

### 缓存架构

**三级缓存机制**（优先级从高到低）：

1. **Redis缓存** (最快，但可能未实现)
2. **PostgreSQL缓存** (`vos_data_cache` 表)
   - 存储VOS API响应结果
   - TTL机制自动过期
   - 缓存命中率高，减少VOS API调用
3. **VOS API** (最慢，最终数据源)

**缓存策略**:
- 话机数据: TTL 5分钟
- 客户数据: TTL 10分钟
- 网关数据: TTL 4小时
- 其他API: TTL 1-60分钟（根据数据更新频率）

## 🔄 数据流程

### 1. 话单同步流程

```
VOS服务器
    │
    │ (定时任务: 每天凌晨1:30)
    ▼
Celery任务: sync_all_instances_cdrs
    │
    │ 1. 查询VOS API获取话单
    │ 2. 数据清洗和转换
    │ 3. 写入ClickHouse
    ▼
ClickHouse (cdrs表)
    │
    │ (按月分区存储)
    │ (自动去重: flow_no)
    ▼
数据就绪，可用于查询和统计
```

### 2. 统计数据计算流程

```
ClickHouse (cdrs表)
    │
    │ (定时任务: 每天凌晨2:30)
    ▼
Celery任务: calculate_all_instances_statistics
    │
    │ 1. 查询ClickHouse统计前一天数据
    │ 2. 按维度聚合计算
    │    - VOS节点级别
    │    - 账户级别
    │    - 网关级别
    │ 3. 计算统计指标
    │    - 总费用、通话时长
    │    - 通话数、接通数
    │    - 接通率
    │ 4. 写入PostgreSQL
    ▼
PostgreSQL (cdr_statistics表)
    │
    │ (统一表，通过statistic_type区分维度)
    ▼
前端查询显示统计结果
```

### 3. VOS数据同步流程

```
VOS API
    │
    │ (定时任务: 根据数据类型)
    ▼
Celery任务
    │
    ├─ sync_all_instances_online_phones (每5分钟)
    ├─ sync_all_instances_customers (每10分钟)
    ├─ sync_all_instances_gateways (每4小时)
    └─ sync_all_vos_common_apis (每1分钟)
    │
    │ 1. 调用VOS API获取数据
    │ 2. 写入PostgreSQL专门表
    │ 3. 写入PostgreSQL缓存表 (vos_data_cache)
    │ 4. 更新Redis缓存（如果启用）
    ▼
PostgreSQL (专门表 + 缓存表)
    │
    ▼
前端查询（优先使用缓存）
```

### 4. API查询流程

```
前端请求
    │
    ▼
FastAPI后端
    │
    │ 1. 检查Redis缓存 (如果启用)
    │ 2. 检查PostgreSQL缓存 (vos_data_cache)
    │ 3. 如果缓存有效 → 直接返回
    │ 4. 如果缓存过期 → 调用VOS API
    │ 5. 更新缓存
    ▼
返回数据
```

## 📊 统计计算公式

### 基础统计指标

#### 1. 总通话记录数 (total_calls)

```sql
SELECT count() as total_calls
FROM cdrs
WHERE vos_id = {vos_id}
  AND vos_uuid = '{vos_uuid}'
  AND toDate(start) >= '{start_date}'
  AND toDate(start) < '{end_date}'
```

**说明**: 统计指定时间范围内的所有话单记录数（包括未接通的呼叫）

#### 2. 接通通话数 (connected_calls)

```sql
SELECT countIf(hold_time > 0) as connected_calls
FROM cdrs
WHERE vos_id = {vos_id}
  AND vos_uuid = '{vos_uuid}'
  AND toDate(start) >= '{start_date}'
  AND toDate(start) < '{end_date}'
```

**说明**: 统计 `hold_time > 0` 的话单记录数（已接通的呼叫）

#### 3. 总通话时长 (total_duration)

```sql
SELECT sumIf(hold_time, hold_time > 0) as total_duration
FROM cdrs
WHERE vos_id = {vos_id}
  AND vos_uuid = '{vos_uuid}'
  AND toDate(start) >= '{start_date}'
  AND toDate(start) < '{end_date}'
```

**说明**: 统计所有接通通话的总时长（秒），只计算 `hold_time > 0` 的记录

#### 4. 总费用 (total_fee)

```sql
SELECT sum(fee) as total_fee
FROM cdrs
WHERE vos_id = {vos_id}
  AND vos_uuid = '{vos_uuid}'
  AND toDate(start) >= '{start_date}'
  AND toDate(start) < '{end_date}'
```

**说明**: 统计所有话单的总费用（包括未接通的呼叫费用）

#### 5. 接通率 (connection_rate)

**公式**:
```
接通率 = (接通通话数 / 总通话记录数) × 100%
```

**代码实现**:
```python
def calculate_connection_rate(total_calls: int, connected_calls: int) -> float:
    """计算接通率（百分比）"""
    if total_calls == 0:
        return 0.0
    return round((connected_calls / total_calls) * 100, 2)
```

**SQL实现**:
```sql
SELECT 
    (countIf(hold_time > 0) * 100.0 / count()) as connection_rate
FROM cdrs
WHERE ...
```

**说明**: 
- 接通率 = 接通通话数 ÷ 总通话记录数 × 100%
- 如果总通话数为0，返回 0%
- 结果保留2位小数

### 多维度统计

#### VOS节点级别统计

统计整个VOS节点的汇总数据：

```sql
SELECT 
    count() as total_calls,
    countIf(hold_time > 0) as connected_calls,
    sumIf(hold_time, hold_time > 0) as total_duration,
    sum(fee) as total_fee
FROM cdrs
WHERE vos_id = {vos_id}
  AND vos_uuid = '{vos_uuid}'
  AND toDate(start) >= '{start_date}'
  AND toDate(start) < '{end_date}'
```

**保存到**: `cdr_statistics` 表，`statistic_type = 'vos'`，`dimension_value = NULL`

#### 账户级别统计

按账户名称分组统计：

```sql
SELECT 
    account_name,
    count() as total_calls,
    countIf(hold_time > 0) as connected_calls,
    sumIf(hold_time, hold_time > 0) as total_duration,
    sum(fee) as total_fee
FROM cdrs
WHERE vos_id = {vos_id}
  AND vos_uuid = '{vos_uuid}'
  AND toDate(start) >= '{start_date}'
  AND toDate(start) < '{end_date}'
  AND account_name != ''
GROUP BY account_name
```

**保存到**: `cdr_statistics` 表，`statistic_type = 'account'`，`dimension_value = account_name`

#### 网关级别统计

按落地网关分组统计：

```sql
SELECT 
    callee_gateway,
    count() as total_calls,
    countIf(hold_time > 0) as connected_calls,
    sumIf(hold_time, hold_time > 0) as total_duration,
    sum(fee) as total_fee
FROM cdrs
WHERE vos_id = {vos_id}
  AND vos_uuid = '{vos_uuid}'
  AND toDate(start) >= '{start_date}'
  AND toDate(start) < '{end_date}'
  AND callee_gateway != ''
GROUP BY callee_gateway
```

**保存到**: `cdr_statistics` 表，`statistic_type = 'gateway'`，`dimension_value = callee_gateway`

### 周期类型计算

#### 日统计 (day)

```python
start_date = statistic_date  # 例如: 2025-01-15
end_date = statistic_date + timedelta(days=1)  # 2025-01-16
# 查询范围: [2025-01-15 00:00:00, 2025-01-16 00:00:00)
```

#### 月统计 (month)

```python
start_date = statistic_date.replace(day=1)  # 2025-01-01
end_date = start_date + relativedelta(months=1)  # 2025-02-01
# 查询范围: [2025-01-01 00:00:00, 2025-02-01 00:00:00)
```

#### 季度统计 (quarter)

```python
quarter = (statistic_date.month - 1) // 3  # 0, 1, 2, 3
start_date = date(statistic_date.year, quarter * 3 + 1, 1)  # 季度首月1号
end_date = start_date + relativedelta(months=3)  # 下一季度首月1号
# 例如: Q1 (1-3月), Q2 (4-6月), Q3 (7-9月), Q4 (10-12月)
```

#### 年统计 (year)

```python
start_date = date(statistic_date.year, 1, 1)  # 2025-01-01
end_date = date(statistic_date.year + 1, 1, 1)  # 2026-01-01
# 查询范围: [2025-01-01 00:00:00, 2026-01-01 00:00:00)
```

## 🚀 快速开始

### 前置要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+, Debian 11+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **内存**: 8GB+ (推荐16GB)
- **磁盘**: 50GB+ (话单数据量大，建议100GB+)
- **CPU**: 4核+ (推荐8核)

### 一键部署（全新服务器）

```bash
# 1. 克隆代码
git clone <your-repo-url>
cd yk-vos

# 2. 执行全新安装脚本
bash scripts/fresh_install.sh
```

部署脚本会自动完成：
1. ✅ 检查系统环境和Docker安装
2. ✅ 创建数据目录并设置权限
3. ✅ 生成配置文件 (`.env`)
4. ✅ 启动数据库服务 (PostgreSQL, ClickHouse, Redis)
5. ✅ 执行数据库初始化SQL
6. ✅ 构建Docker镜像
7. ✅ 启动所有服务
8. ✅ 创建管理员账户

### 访问系统

部署完成后，访问以下地址：

- **前端界面**: http://服务器IP:3000
- **后端API**: http://服务器IP:3001
- **API文档**: http://服务器IP:3001/docs
- **默认账号**: `admin` / `admin123` (首次登录后请立即修改)

### 数据库账号

**PostgreSQL**:
- 用户名: `vos_user`
- 密码: 查看 `.env` 文件中的 `POSTGRES_PASSWORD`
- 数据库: `vosadmin`
- 端口: `5430` (容器内5432)

**ClickHouse**:
- 用户名: `vosadmin`
- 密码: 查看 `.env` 文件中的 `CLICKHOUSE_PASSWORD`
- 数据库: `vos_cdrs`
- HTTP端口: `8123`
- Native端口: `9000`

## 📖 部署指南

### 完整部署流程

#### 1. 环境准备

```bash
# 检查Docker版本
docker --version
docker compose version

# 如果未安装，执行安装脚本会自动安装
```

#### 2. 初始化数据库

数据库初始化由 `scripts/fresh_install.sh` 自动完成，包括：

**PostgreSQL初始化** (`sql/init_database.sql`):
- 创建统一统计表 (`cdr_statistics`)
- 创建版本管理表 (`db_versions`)
- 创建必要的扩展 (uuid-ossp, pg_trgm)

**ClickHouse初始化** (`clickhouse/init/01_create_tables.sql`):
- 创建话单数据库 (`vos_cdrs`)
- 创建话单表 (`cdrs`) - 按月分区
- 创建物化视图（按天统计、账户统计、网关统计）

#### 3. 应用表结构初始化

应用启动时会自动执行 Alembic 数据库迁移，创建以下表：
- 用户表 (`users`)
- VOS实例表 (`vos_instances`)
- 客户表 (`customers`)
- 网关表 (`gateways`)
- 话机表 (`phones`)
- 数据缓存表 (`vos_data_cache`)
- 健康检查表 (`vos_health_checks`)

#### 4. 定时任务配置

Celery Beat 定时任务自动启动，包括：

| 任务名称 | 执行频率 | 说明 |
|---------|---------|------|
| `sync-phones-every-5min` | 每5分钟 | 同步在线话机 |
| `sync-customers-every-10min` | 每10分钟 | 同步客户数据 |
| `sync-cdr-daily-0130` | 每天01:30 | 同步前一天话单 |
| `sync-all-vos-common-apis-every-1min` | 每1分钟 | 通用API数据同步 |
| `sync-all-instances-enhanced-every-4hours` | 每4小时 | 增强版同步（话机、网关、费率、套餐） |
| `sync-all-gateways-every-4hours` | 每4小时 | 网关专用同步 |
| `check-vos-health-every-5min` | 每5分钟 | VOS实例健康检查 |
| `calculate-cdr-statistics-daily` | 每天02:30 | 计算前一天统计数据 |
| `cleanup-expired-cache-daily` | 每天02:00 | 清理过期缓存 |

### 日常维护脚本

```bash
# 日常更新部署
bash scripts/daily_update.sh

# 数据库升级迁移
bash scripts/upgrade_migration.sh

# 数据备份
bash scripts/backup_data.sh
```

## 📂 项目结构

```
yk-vos/
├── backend/                      # 后端服务
│   ├── app/
│   │   ├── alembic/             # 数据库迁移
│   │   ├── core/                # 核心模块
│   │   │   ├── config.py       # 配置管理
│   │   │   ├── db.py           # 数据库连接
│   │   │   ├── vos_client.py   # VOS API客户端
│   │   │   ├── vos_cache_service.py  # 缓存服务
│   │   │   └── vos_sync_enhanced.py  # 同步服务
│   │   ├── models/              # 数据模型
│   │   │   ├── user.py         # 用户模型
│   │   │   ├── vos_instance.py # VOS实例模型
│   │   │   ├── customer.py     # 客户模型
│   │   │   ├── gateway.py      # 网关模型
│   │   │   ├── cdr_statistics.py      # 统计模型（旧）
│   │   │   └── unified_cdr_statistics.py  # 统一统计模型（新）
│   │   ├── routers/             # API路由
│   │   │   ├── auth.py         # 认证路由
│   │   │   ├── vos.py          # VOS管理路由
│   │   │   ├── cdr.py          # 话单查询路由
│   │   │   └── vos_api.py      # VOS API代理路由
│   │   └── tasks/               # Celery任务
│   │       ├── sync_tasks.py   # 同步任务
│   │       ├── cdr_statistics_tasks.py  # 统计任务（旧）
│   │       ├── unified_cdr_statistics_tasks.py  # 统一统计任务（新）
│   │       └── celery_app.py   # Celery配置
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                     # 前端服务
│   ├── app/                     # Next.js页面
│   │   ├── dashboard/          # 仪表盘
│   │   ├── vos/                # VOS管理
│   │   ├── gateway/            # 网关管理
│   │   └── sync-management/    # 同步管理
│   ├── components/             # React组件
│   │   ├── ui/                # UI组件
│   │   └── charts/            # 图表组件
│   └── package.json
│
├── clickhouse/                  # ClickHouse初始化
│   └── init/
│       └── 01_create_tables.sql
│
├── sql/                         # PostgreSQL SQL脚本
│   ├── init_database.sql       # 初始化脚本（统一统计表）
│   ├── create_unified_cdr_statistics_table.sql  # 统一统计表创建脚本
│   ├── migrate_to_unified_cdr_statistics.sql    # 数据迁移脚本
│   ├── upgrade_db_v2.3.sql     # 升级脚本v2.3 (UUID支持)
│   └── upgrade_db_v2.4.sql     # 升级脚本v2.4 (字段修复)
│
├── scripts/                     # 部署脚本
│   ├── fresh_install.sh        # 全新安装脚本
│   ├── upgrade_migration.sh    # 升级迁移脚本
│   ├── daily_update.sh         # 日常更新脚本
│   └── backup_data.sh          # 备份脚本
│
├── data/                        # 数据目录
│   ├── postgres/               # PostgreSQL数据
│   └── clickhouse/             # ClickHouse数据
│
├── docker-compose.yaml          # 服务编排配置
├── docker-compose.base.yaml     # 基础镜像构建
└── README.md                    # 本文档
```

## 📡 API文档

启动服务后，访问以下地址查看API文档：

- **Swagger UI**: http://服务器IP:3001/docs
- **ReDoc**: http://服务器IP:3001/redoc

### 主要API端点

#### 认证相关
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出

#### VOS管理
- `GET /api/v1/vos/instances` - 获取VOS实例列表
- `POST /api/v1/vos/instances` - 创建VOS实例
- `GET /api/v1/vos/instances/{id}` - 获取VOS实例详情
- `GET /api/v1/vos/instances/{id}/statistics` - 获取统计数据

#### 话单查询
- `GET /api/v1/cdr/history` - 查询历史话单
- `GET /api/v1/cdr/export` - 导出话单数据

#### 同步管理
- `POST /api/v1/sync/manual/customer` - 手动触发客户同步
- `POST /api/v1/sync/manual/gateway` - 手动触发网关同步

## 🔧 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f [service_name]
docker compose logs -f backend    # 后端日志
docker compose logs -f frontend   # 前端日志
docker compose logs -f celery-worker  # Celery任务日志
docker compose logs -f celery-beat    # Celery调度日志

# 重启服务
docker compose restart [service_name]
docker compose restart backend

# 停止服务
docker compose down

# 停止并删除数据（⚠️ 危险操作）
docker compose down -v

# 进入容器
docker compose exec backend bash
docker compose exec postgres psql -U vos_user -d vosadmin

# 备份数据库
bash scripts/backup_data.sh

# 查看Celery任务
docker compose exec celery-worker celery -A app.tasks.celery_app inspect active
```

## 🐛 故障排查

### 查看服务日志

```bash
# 查看所有服务日志
docker compose logs --tail=100

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f postgres
docker compose logs -f clickhouse
docker compose logs -f celery-worker
```

### 数据库连接问题

```bash
# 检查PostgreSQL
docker compose exec postgres pg_isready -U vos_user -d vosadmin

# 检查ClickHouse
docker compose exec clickhouse clickhouse-client --query "SELECT 1"

# 检查Redis
docker compose exec redis redis-cli ping
```

### 服务健康检查

```bash
# 检查所有服务健康状态
docker compose ps

# 检查服务是否正常响应
curl http://localhost:3001/health
curl http://localhost:3000
```

### 常见问题

#### 1. 端口被占用

```bash
# 检查端口占用
netstat -tlnp | grep -E '3000|3001|5430|6379|8123|9000'

# 修改 docker-compose.yaml 中的端口映射
```

#### 2. 数据库初始化失败

```bash
# 检查数据库日志
docker compose logs postgres
docker compose logs clickhouse

# 手动执行初始化SQL
docker compose exec -T postgres psql -U vos_user -d vosadmin < sql/init_database.sql
```

#### 3. Celery任务不执行

```bash
# 检查Celery Beat状态
docker compose logs celery-beat

# 检查Celery Worker状态
docker compose logs celery-worker

# 重启Celery服务
docker compose restart celery-beat celery-worker
```

#### 4. 统计数据不更新

```bash
# 检查统计任务日志
docker compose logs celery-worker | grep "统计"

# 手动触发统计
# 在前端VOS详情页面点击"重新计算统计"按钮
# 或通过API调用
curl -X POST http://localhost:3001/api/v1/vos/instances/1/statistics/calculate
```

### 重新部署

如果遇到严重问题，可以完全重新部署：

```bash
# 1. 停止所有服务
docker compose down -v

# 2. 备份数据（如果需要）
bash scripts/backup_data.sh

# 3. 清理数据目录（⚠️ 会删除所有数据）
sudo rm -rf data/postgres/* data/clickhouse/*

# 4. 重新设置权限
sudo chown -R 999:999 data/postgres
sudo chown -R 101:101 data/clickhouse

# 5. 重新部署
bash scripts/fresh_install.sh
```

## 🔒 安全建议

1. **首次登录后立即修改管理员密码**
2. **配置防火墙，只开放必要端口** (3000, 3001)
3. **使用Nginx反向代理并配置HTTPS**
4. **定期备份数据库** (`bash scripts/backup_data.sh`)
5. **修改默认数据库密码** (在 `.env` 文件中)
6. **限制数据库端口外网访问** (PostgreSQL: 5430, ClickHouse: 8123/9000)

## 📄 许可证

MIT License

---

**Made with ❤️ by YK-VOS Team**
