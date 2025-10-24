# 更新日志 (Changelog)

本文档记录 YK-VOS 项目的所有重要变更。

---

## [v2.0.0] - 2025-10-24

### 🔄 架构重构

**重大变更**: 从 TimescaleDB 迁移到 ClickHouse 双数据库架构

#### 新增
- ✨ **ClickHouse 集成**: 使用 ClickHouse 存储海量话单数据
  - 支持按月自动分区
  - 自动去重（ReplacingMergeTree）
  - 物化视图实时统计（按天、按账户、按网关）
  - 跳数索引加速查询

- 📊 **话单查询优化**:
  - 优先查询 ClickHouse 本地数据
  - 自动降级到 VOS API
  - 后台异步存储 VOS API 返回的数据到 ClickHouse

- 🚀 **一键部署脚本**:
  - 自动创建数据目录并设置权限
  - 自动生成随机密码
  - 完整的健康检查
  - 部署完成后显示访问信息和凭证

- 📦 **数据持久化**:
  - PostgreSQL 数据映射到 `./data/postgres/`
  - ClickHouse 数据映射到 `./data/clickhouse/`
  - 方便备份和迁移

#### 变更
- 🔧 **配置简化**:
  - 保留 `docker-compose.yaml` 和 `docker-compose.base.yaml`
  - 移除 `docker-compose.clickhouse.yaml`（功能合并到主文件）
  - 移除 `deploy-clickhouse.sh`（功能合并到 `deploy.sh`）

- 🗄️ **数据库分工明确**:
  - PostgreSQL: 配置数据（用户、VOS实例、健康检查、同步配置等）
  - ClickHouse: 话单数据（CDR 记录，支持亿级数据量）

- 🔐 **安全增强**:
  - 默认生成随机密码
  - 部署完成后显示数据库凭证
  - 提醒修改默认管理员密码

#### 移除
- ❌ 移除 TimescaleDB 依赖
- ❌ 移除 TimescaleDB 迁移脚本 (`0009_timescale_cdrs.py`)
- ❌ 移除 PostgreSQL 中的 `cdrs` 表（话单数据）

#### 修复
- 🐛 修复数据库迁移链依赖问题
- 🐛 修复新部署环境的权限问题
- 🐛 修复话单导出功能在本地无数据时失败的问题

#### 文档
- 📚 新增 `FRESH_DEPLOYMENT.md` - 全新部署指南
- 📚 更新 `README.md` - 更新架构说明
- 📚 保留 `CLICKHOUSE_MIGRATION.md` - ClickHouse 迁移文档
- 📚 保留 `DATA_STORAGE.md` - 数据存储说明

---

## [v1.5.0] - 2025-10-23

### 新增
- ✨ **VOS 健康检查**: 
  - 后台定时（每5分钟）检查 VOS 实例 API 连通性
  - 仪表盘显示 VOS 状态（健康/异常/未知）
  - 显示响应时间和错误信息

- 📊 **话单查询优化**:
  - 移除"最小通话时长"查询条件
  - 修复主叫号码显示（优先 `callerAccessE164`）
  - 时间显示精确到秒（YYYY-MM-DD HH:mm:ss）
  - 支持单日查询（开始日期 = 结束日期）

- 📤 **话单导出增强**:
  - 修复导出无数据问题
  - 添加详细调试日志
  - 统一查询和导出逻辑

### 变更
- 🔧 **前端 API 代理**:
  - 配置 Next.js rewrites 代理 API 请求
  - 解决浏览器跨域问题
  - 环境变量配置优化

- 🗄️ **数据库迁移自动化**:
  - 集成 Alembic 到部署脚本
  - 新增数据库迁移菜单选项
  - 自动检查并执行迁移

### 修复
- 🐛 修复前端登录 `ERR_CONNECTION_REFUSED` 错误
- 🐛 修复 API 代理 404 错误
- 🐛 修复话单导出只有表头无数据的问题
- 🐛 修复 Alembic 迁移版本依赖错误

---

## [v1.0.0] - 2025-10-22

### 初始版本
- ⚙️ **基础功能**:
  - 用户认证和授权
  - VOS 实例管理
  - 话单查询和导出
  - 客户管理
  - 数据缓存管理

- 🏗️ **技术栈**:
  - 前端: Next.js 14, React, Tailwind CSS
  - 后端: FastAPI, SQLAlchemy, Celery
  - 数据库: PostgreSQL + TimescaleDB
  - 缓存: Redis
  - 容器化: Docker + Docker Compose

- 📦 **部署方式**:
  - Docker 容器化部署
  - 基础镜像 + 代码挂载
  - 支持热重载开发

---

## 版本说明

### 版本号规则

遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/)：

- **主版本号 (MAJOR)**: 不兼容的 API 修改
- **次版本号 (MINOR)**: 向下兼容的功能性新增
- **修订号 (PATCH)**: 向下兼容的问题修正

### 图例

- ✨ 新增功能
- 🔧 配置变更
- 🐛 Bug 修复
- 📚 文档更新
- 🔄 重构
- ❌ 移除功能
- 🔐 安全更新
- 📊 性能优化
- 🚀 部署相关

---

**维护者**: YK-VOS 开发团队  
**更新频率**: 随版本发布更新

