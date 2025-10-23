# YK-VOS - VOS3000 管理与分析平台

一个现代化的 VOS3000 管理和分析平台，提供实时监控、历史话单查询和智能数据分析功能。

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11-green.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)

---

## ✨ 核心特性

### 🚀 性能优化
- ⚡ **极速查询**：历史话单查询速度提升 **20-50 倍**（本地 < 10ms）
- 📉 **降低 VOS 压力**：80%+ 查询走本地数据库
- 🔍 **智能索引**：5 个数据库索引覆盖所有查询场景

### 🎨 用户体验
- 📝 **智能表单**：自动识别参数类型，时间默认最近 3 天
- 📄 **分页显示**：默认 20 条/页，流畅浏览大数据
- 🔄 **三级查询**：本地数据库 → 缓存 → VOS API 智能切换

### 💼 业务功能
- 📊 **实时监控**：在线话机、网关、通话状态实时同步
- 📞 **话单分析**：历史 CDR 数据查询和统计分析
- 👥 **客户管理**：账户信息、缴费记录、消费统计
- 🔐 **安全认证**：JWT Token + 角色权限管理

### 🛠️ 技术优势
- 🐳 **容器化部署**：Docker Compose 一键部署
- 🔄 **自动同步**：Celery 定时任务后台同步
- 📈 **数据可视化**：Recharts 图表展示
- 🌐 **37 个 VOS API**：统一查询界面

---

## 🏗️ 技术栈

### 后端
- **FastAPI** - 现代、高性能的 Python Web 框架
- **SQLAlchemy** - ORM 数据库操作
- **PostgreSQL** - 主数据库（支持 JSONB）
- **Redis** - 缓存和消息队列
- **Celery** - 分布式任务队列
- **Alembic** - 数据库迁移工具

### 前端
- **Next.js 14** - React 框架（App Router）
- **Tailwind CSS** - 实用优先的 CSS 框架
- **Recharts** - 数据可视化
- **TypeScript** - 类型安全

---

## 🚀 快速开始

### 前置要求
- **操作系统**：Debian 10+ 或 Ubuntu 20.04+
- **Docker**：20.10+
- **Docker Compose**：2.0+
- **内存**：2GB+（推荐 4GB）
- **磁盘**：10GB+
- **端口**：3000（前端）、8000（后端）

> 🚀 **已配置国内镜像加速**：使用 `docker.1ms.run`、`mirrors.ustc.edu.cn`、`pypi.tuna.tsinghua.edu.cn` 等国内镜像源，部署速度提升 5-10 倍！详见 [MIRROR_CONFIG.md](./MIRROR_CONFIG.md)

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd yk-vos
```

### 2. 配置环境变量

创建 `backend/.env` 文件：
```bash
# 数据库配置
POSTGRES_USER=vos_user
POSTGRES_PASSWORD=your_strong_password
POSTGRES_DB=vosadmin
DATABASE_URL=postgresql://vos_user:your_strong_password@postgres:5432/vosadmin

# JWT 配置
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis 配置
REDIS_URL=redis://redis:6379/0

# Celery 配置
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

创建 `frontend/.env.local` 文件：
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 启动服务

#### 全新服务器初始化部署（首次） ⭐

```bash
chmod +x init-deploy.sh
./init-deploy.sh
```

**自动完成**：
- ✅ 检查系统环境（Debian/Ubuntu）
- ✅ 创建配置文件
- ✅ 构建基础镜像
- ✅ 启动所有服务
- ✅ 初始化数据库
- ✅ 验证部署结果

#### 已有环境启动

如果已完成初始化，直接启动：

```bash
# 启动所有服务
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

### 4. 访问应用

- 🌐 **前端界面**：http://localhost:3000
- 📚 **API 文档**：http://localhost:8000/docs
- ❤️ **健康检查**：http://localhost:8000/health

### 5. 登录系统

**默认管理员账号**：
- 用户名：`admin`
- 密码：`admin123`

> ⚠️ **重要**：首次登录后请立即修改默认密码！

---

## 📊 核心功能

### 1. 实时监控
- **在线话机**：实时显示在线话机数量和状态
- **网关监控**：对接网关和落地网关状态
- **通话监控**：当前通话列表和统计
- **系统性能**：并发数、队列长度监控

### 2. 历史话单查询 ⚡

**三级智能查询**：
```
用户查询
   ↓
【优先】本地数据库 (< 10ms)
   ↓ (未找到)
【备选】VOS API (200-500ms)
   ↓
【自动】数据存储
```

**查询选项**：
- 时间范围查询（默认最近 3 天）
- 主叫/被叫号码查询
- 客户账号过滤
- 网关过滤
- 强制 VOS 实时查询

**性能对比**：
- 本地查询：**< 10ms** ⚡
- VOS 查询：200-500ms
- 提升：**20-50 倍**

### 3. VOS API 查询

**37 个 VOS 接口统一管理**：

| 类别 | 接口数 | 说明 |
|-----|-------|------|
| 账户管理 | 5 | 账户查询、缴费记录、消费统计 |
| 话机管理 | 3 | 话机查询、在线状态 |
| 网关管理 | 4 | 对接网关、落地网关 |
| 通话管理 | 3 | 当前通话、历史话单、性能 |
| 费率与套餐 | 3 | 费率组、费率、套餐 |
| 系统管理 | 2 | 软交换、告警 |

**智能表单**：
- ✅ 自动识别参数类型
- ✅ 时间默认最近 3 天
- ✅ 数组逗号分隔输入
- ✅ 必填字段标识
- ✅ 实时 JSON 预览

**分页显示**：
- 默认 20 条/页
- 支持 10/20/50/100 切换
- 流畅浏览大数据

### 4. 客户管理
- 客户信息查询
- 缴费记录查询
- 消费统计分析
- 电话簿管理

---

## 🔧 部署和更新

### 快速更新（日常使用） ⚡

适用于修改代码后的快速部署：

```bash
# 方式一：使用快速更新脚本（推荐）
bash quick-update.sh

# 方式二：手动执行
git pull && docker-compose restart backend frontend
```

### 完整升级（重要更新） 🔄

适用于有数据库变更或依赖更新：

```bash
# 使用完整升级脚本
bash upgrade.sh
```

**自动完成**：
- ✅ 备份数据库
- ✅ 拉取最新代码
- ✅ 执行数据库迁移
- ✅ 重启所有服务
- ✅ 验证部署结果

### 一键部署工具（菜单式） 🎛️

交互式部署工具，提供多种操作：

```bash
bash deploy.sh
```

**功能菜单**：
1. 快速更新（拉代码 + 重启服务）
2. 完整升级（备份 + 拉代码 + 迁移 + 重启）
3. 仅重启服务
4. 查看服务状态
5. 查看日志

---

## 🔧 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看实时日志（所有服务）
docker-compose logs -f

# 只查看后端日志
docker-compose logs -f backend

# 只查看前端日志
docker-compose logs -f frontend

# 重启服务（修改代码后）
docker-compose restart backend
docker-compose restart frontend

# 重启所有服务
docker-compose restart

# 停止服务
docker-compose stop

# 停止并删除容器（保留数据）
docker-compose down

# 完全清理（删除数据卷，慎用）
docker-compose down -v

# 进入后端容器
docker-compose exec backend bash

# 手动执行数据库迁移
docker-compose exec backend bash -c "cd /srv/app && alembic upgrade head"

# 查看数据库
docker-compose exec postgres psql -U vos_user -d vosadmin
```

---

## 🔄 自动定时任务

系统包含以下自动执行的定时任务（Celery Beat）：

| 任务 | 执行频率 | 说明 |
|-----|---------|------|
| 同步 VOS 常用 API | 每 1 分钟 | 在线话机、网关、性能等 |
| 同步增强实例数据 | 每 2 分钟 | 话机、网关详细信息 |
| 清理过期缓存 | 每天 02:00 | 自动清理过期的缓存数据 |

**查看任务执行情况**：
```bash
# 查看 Celery Worker 日志
docker-compose logs -f celery-worker

# 查看 Celery Beat 日志
docker-compose logs -f celery-beat
```

---

## 📦 升级部署

### 快速升级

```bash
# 拉取最新代码
git pull

# 停止服务
docker-compose down

# 重新构建并启动（自动执行数据库迁移）
docker-compose up -d --build
```

### 一键升级脚本

**Linux / macOS**：
```bash
chmod +x upgrade.sh
./upgrade.sh
```

**Windows (PowerShell)**：
```powershell
.\upgrade.ps1
```

**脚本功能**：
- ✅ 自动备份数据库
- ✅ 拉取最新代码
- ✅ 构建新镜像
- ✅ 执行数据库迁移
- ✅ 验证部署结果

### 详细升级指南

查看完整的升级部署文档：[UPGRADE_GUIDE.md](./UPGRADE_GUIDE.md)

包含：
- 详细部署步骤
- 故障排查指南
- 回滚操作
- 性能验证
- 部署检查清单

---

## 🏗️ 架构设计

### 依赖镜像 + 代码挂载架构

**核心理念**：
- 🎯 **基础镜像**：只包含系统依赖和 Python/Node 包（`Dockerfile.base`）
- 📂 **代码挂载**：代码通过卷映射进容器（实时同步）
- ⚡ **快速部署**：修改代码后只需重启容器（< 3秒）
- 🔄 **自动重载**：后端 `--reload`，前端 `dev` 模式

**部署流程**：

```
1. 首次部署（构建基础镜像）
   └─> ./init-deploy.sh
       ├─> 构建依赖镜像（5-10分钟，只需一次）
       └─> 启动容器并挂载代码

2. 修改代码（日常开发）
   └─> 编辑 backend/app/xxx.py 或 frontend/app/xxx.tsx
       └─> 自动重载（< 3秒）⚡
       └─> 刷新浏览器测试

3. 更新依赖（很少发生）
   └─> 修改 requirements.txt 或 package.json
       └─> 重新构建基础镜像
       └─> docker-compose -f docker-compose.base.yaml build
```

**性能对比**：

| 操作 | 传统方式 | 当前架构 | 提升 |
|-----|---------|----------|------|
| 修改代码后部署 | 重新构建镜像（3-5分钟） | 重启容器（< 3秒） | **100倍+** ⚡ |
| 首次构建 | 5-10分钟 | 5-10分钟 | 相同 |
| 镜像大小 | 800MB+（含代码） | 300MB（只含依赖） | 减少 60% |

## 🏛️ 项目结构

```
yk-vos/
├── backend/                  # 后端服务
│   ├── Dockerfile           # 生产环境镜像
│   ├── Dockerfile.dev       # 开发环境镜像（只含依赖）
│   ├── app/
│   │   ├── core/            # 核心模块
│   │   │   ├── db.py        # 数据库连接
│   │   │   ├── vos_client.py         # VOS API 客户端
│   │   │   ├── vos_cache_service.py  # 缓存服务
│   │   │   └── vos_sync_enhanced.py  # 增强同步服务
│   │   ├── models/          # 数据模型
│   │   │   ├── user.py      # 用户模型
│   │   │   ├── vos_instance.py      # VOS 实例
│   │   │   ├── cdr.py               # 话单模型
│   │   │   ├── vos_data_cache.py    # 通用缓存
│   │   │   ├── phone_enhanced.py    # 增强话机模型
│   │   │   └── gateway.py           # 网关模型
│   │   ├── routers/         # API 路由
│   │   │   ├── auth.py      # 认证路由
│   │   │   ├── vos.py       # VOS 管理
│   │   │   ├── vos_api.py   # VOS API 代理
│   │   │   └── cdr.py       # 话单查询
│   │   ├── tasks/           # Celery 任务
│   │   │   ├── celery_app.py        # Celery 配置
│   │   │   └── sync_tasks.py        # 同步任务
│   │   └── alembic/         # 数据库迁移
│   │       └── versions/    # 迁移脚本
│   ├── docker-entrypoint.sh # 容器启动脚本
│   ├── Dockerfile           # Docker 镜像
│   └── requirements.txt     # Python 依赖
├── frontend/                # 前端应用
│   ├── Dockerfile           # 生产环境镜像
│   ├── Dockerfile.dev       # 开发环境镜像（只含依赖）
│   ├── app/                 # Next.js 页面
│   │   ├── page.tsx         # 首页（仪表盘）
│   │   ├── vos/             # VOS 节点管理
│   │   ├── vos-api/         # VOS API 查询
│   │   ├── cdr/             # 历史话单
│   │   ├── customers/       # 客户管理
│   │   └── cache/           # 缓存管理
│   ├── components/          # React 组件
│   │   ├── VosApiParamForm.tsx     # 智能参数表单
│   │   ├── CacheManagement.tsx     # 缓存管理
│   │   └── AuthGuard.tsx           # 认证守卫
│   ├── contexts/            # React Context
│   │   └── VOSContext.tsx   # VOS 实例上下文
│   └── lib/                 # 工具库
│       └── api.ts           # API 客户端
├── docker-compose.base.yaml  # 基础镜像构建配置
├── docker-compose.yaml       # 服务编排配置（挂载代码）
├── data/                    # 数据目录（本地映射）
│   └── postgres/           # PostgreSQL 数据
├── init-deploy.sh            # 全新服务器初始化脚本
├── upgrade.sh                # 完整升级脚本（带备份）
├── deploy.sh                 # 一键部署工具（菜单式）
├── quick-update.sh           # 快速更新脚本（日常使用）
├── vos3000.json             # VOS API 规范
├── README.md                # 本文档（完整指南）
├── QUICKSTART.md            # 快速开始（新手推荐）
├── DEPLOY_GUIDE.md          # 详细部署说明
└── UPGRADE_GUIDE.md         # 升级指南
```

---

## 💾 数据管理

### PostgreSQL 数据

**存储位置**：
- **本地目录**：`./data/postgres`
- **容器路径**：`/var/lib/postgresql/data`
- **优势**：方便备份、迁移和查看

**备份数据**：
```bash
# 方式一：目录备份（需停止服务）
docker-compose down
tar -czf postgres-backup-$(date +%Y%m%d).tar.gz data/postgres/
docker-compose up -d

# 方式二：pg_dump（推荐，无需停服）
docker-compose exec postgres pg_dump -U vos_user vosadmin > backup-$(date +%Y%m%d).sql
```

**恢复数据**：
```bash
# 从 SQL 备份恢复
docker-compose exec -T postgres psql -U vos_user vosadmin < backup.sql

# 从目录备份恢复
docker-compose down
rm -rf data/postgres
tar -xzf postgres-backup-20240101.tar.gz
docker-compose up -d
```

**迁移到新服务器**：
```bash
# 旧服务器
tar -czf vos-data.tar.gz data/

# 新服务器
tar -xzf vos-data.tar.gz
docker-compose up -d
```

详细说明请查看：[data/README.md](./data/README.md)

---

## 🔐 安全建议

### 必做事项
1. ✅ **修改默认密码**：登录后立即修改管理员密码
2. ✅ **更新密钥**：修改 `backend/.env` 中的 `SECRET_KEY`
3. ✅ **强密码**：使用强密码保护数据库
4. ✅ **限制 CORS**：生产环境配置允许的来源
5. ✅ **保护数据目录**：设置合适的权限 `chmod 700 data/postgres`

### 生产环境配置

**后端 `.env`**：
```bash
# 使用强密钥
SECRET_KEY=$(openssl rand -hex 32)

# 生产数据库
DATABASE_URL=postgresql://vos_user:strong_password@db_host:5432/vosadmin

# CORS 配置（限制允许的来源）
CORS_ORIGINS=["https://yourdomain.com"]
```

**前端 `.env.local`**：
```bash
# 使用实际的 API 地址
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## 🐛 故障排查

### 常见问题

#### 1. 前端无法连接后端

**症状**：页面显示"网络错误"

**解决方案**：
```bash
# 检查后端是否启动
docker-compose ps backend

# 检查健康状态
curl http://localhost:8000/health

# 查看后端日志
docker-compose logs backend
```

#### 2. 数据库连接失败

**症状**：后端日志显示"could not connect to server"或"database does not exist"

**解决方案**：
```bash
# 检查 PostgreSQL 是否启动
docker-compose ps postgres

# 检查数据库连接
docker-compose exec postgres pg_isready -U vos_user -d vosadmin

# 重启数据库
docker-compose restart postgres
```

#### 2.1 数据库为空（无表）

**症状**：登录数据库发现没有任何表，Alembic 迁移未执行

**解决方案**：

**方法一：一键修复（推荐）**
```bash
# 使用自动修复脚本
chmod +x fix-empty-db.sh
./fix-empty-db.sh
```

**方法二：诊断排查**
```bash
# 运行诊断脚本
chmod +x check-migration.sh
./check-migration.sh
```

**方法三：手动执行迁移**
```bash
# 使用手动迁移脚本
chmod +x manual-migrate.sh
./manual-migrate.sh
```

**方法四：进入容器手动修复**
```bash
# 1. 进入后端容器
docker-compose exec backend bash

# 2. 进入 Alembic 目录
cd /srv/app

# 3. 查看当前迁移状态
alembic current

# 4. 执行迁移
alembic upgrade head

# 5. 退出容器
exit

# 6. 验证表已创建
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt"
```

**诊断脚本说明**：

项目提供了三个诊断脚本来帮助排查和修复数据库问题：

- **`fix-empty-db.sh`** - 一键修复空数据库，自动执行迁移和创建管理员账户
- **`check-migration.sh`** - 全面诊断数据库迁移状态，输出详细信息
- **`manual-migrate.sh`** - 手动执行数据库迁移

#### 3. Celery 任务不执行

**症状**：定时同步不工作

**解决方案**：
```bash
# 检查 Celery Worker
docker-compose logs celery-worker

# 检查 Celery Beat
docker-compose logs celery-beat

# 检查 Redis 连接
docker-compose exec redis redis-cli ping

# 重启 Celery 服务
docker-compose restart celery-worker celery-beat
```

#### 4. 端口冲突

**症状**：容器启动失败"port is already allocated"

**解决方案**：
修改 `docker-compose.yml` 中的端口映射：
```yaml
services:
  frontend:
    ports:
      - "3001:3000"  # 改为 3001
  backend:
    ports:
      - "8001:8000"  # 改为 8001
```

#### 5. 查询很慢

**症状**：历史话单查询耗时很长

**解决方案**：
```bash
# 验证索引是否创建
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\d cdrs"

# 应该看到 5 个 idx_cdr_* 索引

# 如果没有，手动执行迁移
docker-compose exec backend alembic upgrade head
```

---

## 📊 性能优化

### 查询性能对比

| 功能 | 优化前 | 优化后 | 提升 |
|-----|-------|--------|------|
| 历史话单查询 | 200-500ms | **< 10ms** | **20-50倍** ⚡ |
| VOS 压力 | 100% | **< 20%** | **降低 80%** 📉 |
| 参数输入 | JSON 文本 | **可视化表单** | **体验提升 100%** 🎨 |
| 数据浏览 | 全部加载 | **分页 20 条** | **流畅无卡顿** 📄 |

### 数据库索引

CDR 表已优化的索引：
- `idx_cdr_vos_time` - (vos_id, start_time) 复合索引
- `idx_cdr_caller` - 主叫号码索引
- `idx_cdr_callee` - 被叫号码索引
- `idx_cdr_caller_gateway` - 主叫网关索引
- `idx_cdr_callee_gateway` - 被叫网关索引

### 缓存策略

- **通用缓存表**：vos_data_cache（JSONB 存储）
- **业务专用表**：phones_enhanced、gateways、fee_rate_groups、suites
- **TTL 管理**：自动过期，定时清理
- **双写策略**：同时更新缓存和业务表

---

## 📝 开发指南

### 修改代码

代码通过挂载映射到容器，修改后自动生效：

```bash
# 1. 修改代码
# 后端：编辑 backend/app/xxx.py
# 前端：编辑 frontend/app/xxx.tsx

# 2. 代码自动重载（< 3秒）
# 后端：FastAPI --reload 模式
# 前端：Next.js dev 模式

# 3. 查看效果
# 刷新浏览器即可
```

### 更新依赖

如果修改了依赖文件：

```bash
# 修改 requirements.txt 或 package.json 后

# 重新构建基础镜像
docker-compose -f docker-compose.base.yaml build

# 重启服务
docker-compose restart
```

### 数据库迁移

**创建新迁移**：
```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
```

**应用迁移**：
```bash
docker-compose exec backend alembic upgrade head
```

**回滚迁移**：
```bash
docker-compose exec backend alembic downgrade -1
```

**查看迁移历史**：
```bash
docker-compose exec backend alembic history
```

### 添加新的 VOS API

1. 在 `vos3000.json` 中添加接口定义
2. 在 `frontend/app/vos-api/page.tsx` 中添加接口配置：
```typescript
{
  name: 'GetNewApi',
  label: '新接口',
  description: '接口说明',
  params: [
    { name: 'param1', type: 'string' as const, required: true, description: '参数1' }
  ]
}
```
3. 重启前端服务即可

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发流程
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](./LICENSE) 文件。

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的 Web 框架
- [Next.js](https://nextjs.org/) - React 生产框架
- [VOS3000](http://www.kunshi.com.cn/) - 昆石 VOS 软交换平台
- [PostgreSQL](https://www.postgresql.org/) - 强大的开源数据库
- [Redis](https://redis.io/) - 内存数据库
- [Celery](https://docs.celeryq.dev/) - 分布式任务队列

---

## 📚 文档导航

### 🚀 快速入门
- **[QUICKSTART.md](./QUICKSTART.md)** - 5 分钟快速开始（推荐新手）
  - 一键部署脚本
  - 基本使用命令
  - 常见问题

### 📖 详细文档
- **[README.md](./README.md)** - 完整使用指南（本文档）
  - 功能特性
  - 架构设计
  - 开发指南
  - 性能优化

- **[DEPLOY_GUIDE.md](./DEPLOY_GUIDE.md)** - 详细部署说明
  - 手动部署步骤
  - 故障排查
  - 安全配置

- **[UPGRADE_GUIDE.md](./UPGRADE_GUIDE.md)** - 升级指南
  - 数据库迁移
  - 性能基准
  - 升级检查清单

### 🔧 技术文档
- **[vos3000.json](./vos3000.json)** - VOS API 规范（Swagger 2.0）
- **[MIRROR_CONFIG.md](./MIRROR_CONFIG.md)** - 镜像加速配置说明
- **[SCRIPTS_GUIDE.md](./SCRIPTS_GUIDE.md)** - 部署脚本使用指南

---

## 📞 支持

- 🐛 **问题反馈**：[提交 Issue](https://github.com/your-repo/issues)
- 💬 **技术交流**：欢迎提问和讨论

---

**祝您使用愉快！** 🎉
