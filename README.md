# YK-VOS - VOS3000 管理与分析平台

一个现代化的 VOS3000 管理和分析平台，提供实时监控、历史话单查询和智能数据分析功能。

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11-green.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)
[![TimescaleDB](https://img.shields.io/badge/timescaledb-enabled-orange.svg)](https://www.timescale.com/)

---

## ✨ 核心特性

### 🚀 性能优化
- ⚡ **极速查询**：历史话单查询速度提升 **20-50 倍**（本地 < 10ms）
- 📉 **降低 VOS 压力**：80%+ 查询走本地数据库
- 🗄️ **时序数据库**：TimescaleDB 自动分区、压缩，支持上亿级话单
- 🔍 **智能索引**：复合索引覆盖所有查询场景

### 🎨 用户体验
- 📝 **智能表单**：自动识别参数类型，时间默认最近 3 天
- 📄 **分页显示**：默认 20 条/页，流畅浏览大数据
- 🔄 **三级查询**：本地数据库 → 缓存 → VOS API 智能切换
- 🔐 **会话管理**：自动超时登出，安全可靠

### 💼 业务功能
- 📊 **实时监控**：在线话机、网关、通话状态实时同步
- 📞 **话单分析**：历史 CDR 数据查询和统计分析（上亿级数据优化）
- 👥 **客户管理**：账户信息、缴费记录、消费统计、自动同步
- 🔧 **系统设置**：VOS 节点管理、数据同步配置、缓存管理
- 🌐 **37 个 VOS API**：统一查询界面

### 🛠️ 技术优势
- 🐳 **容器化部署**：Docker Compose 一键部署
- 🔄 **自动同步**：Celery 定时任务后台同步（可配置 Cron 表达式）
- 📈 **数据可视化**：Recharts 图表展示
- 🗜️ **自动压缩**：30 天后自动压缩，1 年后自动删除
- 🇨🇳 **国内加速**：使用 docker.1ms.run、清华源等镜像，部署速度提升 5-10 倍

---

## 🏗️ 技术栈

### 后端
- **FastAPI** - 现代、高性能的 Python Web 框架
- **SQLAlchemy** - ORM 数据库操作
- **TimescaleDB** - 时序数据库（基于 PostgreSQL）
- **Redis** - 缓存和消息队列
- **Celery** - 分布式任务队列
- **Alembic** - 数据库迁移工具

### 前端
- **Next.js 14** - React 框架（App Router）
- **Tailwind CSS** - 实用优先的 CSS 框架
- **Recharts** - 数据可视化
- **TypeScript** - 类型安全
- **Axios** - HTTP 客户端

---

## 🚀 快速开始

### 前置要求
- **操作系统**：Debian 10+ 或 Ubuntu 20.04+
- **Docker**：20.10+
- **Docker Compose**：2.0+
- **内存**：4GB+（推荐 8GB）
- **磁盘**：20GB+
- **端口**：3000（前端）、8000（后端）、5430（TimescaleDB）、6379（Redis）

### 初始化部署（新服务器）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd yk-vos

# 2. 执行初始化部署脚本
chmod +x init-deploy.sh
./init-deploy.sh
```

脚本会自动完成以下操作：
1. ✅ 检查系统环境（Docker、Docker Compose）
2. 📝 创建配置文件（`.env`）
3. 🏗️ 构建基础镜像（使用国内镜像加速）
4. 🚀 启动所有服务（TimescaleDB、Redis、Backend、Frontend、Celery）
5. 🗄️ 初始化数据库（创建表、索引、TimescaleDB 超表）
6. 👤 创建管理员账户（admin / admin123）
7. ✅ 验证部署（健康检查）

**部署完成后**：
- 前端地址：`http://<服务器IP>:3000`
- 后端API：`http://<服务器IP>:8000`
- 默认账户：`admin` / `admin123`（首次登录后请修改密码）

### 日常更新部署

使用交互式部署工具：

```bash
chmod +x deploy.sh
./deploy.sh
```

菜单选项：
1. **快速更新**：拉取代码 + 重启服务（适用于代码小改动）
2. **完整升级**：备份数据库 + 拉取代码 + 数据库迁移 + 重启服务（适用于大版本升级）
3. **仅重启服务**：重启所有 Docker 容器
4. **查看服务状态**：查看所有容器运行状态
5. **查看日志**：查看各服务日志

---

## 📂 项目结构

```
yk-vos/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── alembic/           # 数据库迁移脚本
│   │   ├── core/              # 核心模块（配置、数据库、VOS客户端）
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── routers/           # FastAPI 路由
│   │   ├── tasks/             # Celery 任务
│   │   └── main.py            # 应用入口
│   ├── docker-entrypoint.sh   # Docker 入口脚本
│   ├── Dockerfile             # 生产环境 Dockerfile
│   ├── Dockerfile.base        # 基础镜像 Dockerfile
│   └── requirements.txt       # Python 依赖
│
├── frontend/                   # 前端服务
│   ├── app/                   # Next.js 页面和路由
│   ├── components/            # React 组件
│   ├── contexts/              # React Context
│   ├── lib/                   # 工具函数
│   ├── Dockerfile             # 生产环境 Dockerfile
│   ├── Dockerfile.base        # 基础镜像 Dockerfile
│   └── package.json           # Node.js 依赖
│
├── data/                       # 数据持久化目录
│   └── postgres/              # TimescaleDB 数据（本地映射）
│
├── docker-compose.base.yaml   # 基础镜像构建配置
├── docker-compose.yaml        # 服务编排配置
├── postgresql.conf            # TimescaleDB 性能优化配置
├── init-deploy.sh             # 初始化部署脚本
├── deploy.sh                  # 日常部署脚本
└── README.md                  # 项目文档
```

---

## ⚙️ 配置说明

### 环境变量

创建 `backend/.env` 文件：

```bash
# 数据库配置
POSTGRES_USER=vos_user
POSTGRES_PASSWORD=your_strong_password_here
POSTGRES_DB=vosadmin
DATABASE_URL=postgresql://vos_user:your_strong_password_here@postgres:5432/vosadmin

# JWT 配置
SECRET_KEY=your-secret-key-change-in-production-at-least-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Redis 配置
REDIS_URL=redis://redis:6379/0

# Celery 配置
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

**重要**：
- 生产环境必须修改 `POSTGRES_PASSWORD` 和 `SECRET_KEY`
- `SECRET_KEY` 建议至少 32 个字符，可使用：`openssl rand -hex 32`

### Docker Compose 配置

`docker-compose.yaml` 中的关键配置：

```yaml
services:
  postgres:
    image: docker.1ms.run/timescale/timescaledb:latest-pg15
    volumes:
      - ./data/postgres:/var/lib/postgresql/data  # 本地数据映射
      - ./postgresql.conf:/etc/postgresql/postgresql.conf:ro
    ports:
      - "5430:5432"  # 避免与本地 PostgreSQL 冲突
    environment:
      TIMESCALEDB_TELEMETRY: "off"
      TS_TUNE_MEMORY: "4GB"  # 根据服务器内存调整
      TS_TUNE_NUM_CPUS: "2"  # 根据服务器 CPU 调整
    shm_size: 2gb  # TimescaleDB 共享内存
```

**性能调优**：
- 4GB 内存服务器：`TS_TUNE_MEMORY: "2GB"`
- 8GB 内存服务器：`TS_TUNE_MEMORY: "4GB"`
- 16GB 内存服务器：`TS_TUNE_MEMORY: "8GB"`

---

## 📊 数据同步

### 自动同步任务

系统会自动执行以下同步任务（通过 Celery Beat 调度）：

| 任务类型 | 默认频率 | 说明 |
|---------|---------|-----|
| 客户数据同步 | 每 2 分钟 | 同步所有客户账户信息 |
| 话机数据同步 | 每 2 分钟 | 同步所有话机状态 |
| 网关数据同步 | 每 2 分钟 | 同步所有网关信息 |
| 通用 API 同步 | 每 1 分钟 | 同步常用 VOS API 数据 |
| 缓存清理 | 每天 1 次 | 清理过期缓存数据 |

### 配置同步任务

在"系统设置 → 数据同步配置"中，可以：
- ✅ 启用/禁用同步任务
- ⏰ 修改 Cron 表达式（自定义执行频率）
- 📝 查看任务执行历史

**Cron 表达式示例**：
```
*/5 * * * *    # 每 5 分钟执行一次
0 */2 * * *    # 每 2 小时执行一次
0 2 * * *      # 每天凌晨 2 点执行
0 0 * * 0      # 每周日凌晨执行
```

### 新增 VOS 节点自动同步

添加新 VOS 节点后，系统会自动执行以下操作：

1. **立即同步客户数据**（全量）
2. **分批同步历史话单**（最近 7 天，每天一个批次，间隔 30 秒）
   - 避免一次性拉取大量数据导致超时
   - 可在业务低峰期手动触发更多天数的同步

---

## 🗄️ 数据库架构

### 核心表结构

| 表名 | 类型 | 说明 | 特点 |
|-----|------|------|------|
| `cdrs` | TimescaleDB 超表 | 历史话单记录 | 按时间自动分区、压缩 |
| `customers` | 普通表 | 客户账户信息 | 自动同步 |
| `vos_instances` | 普通表 | VOS 节点配置 | 多节点管理 |
| `vos_data_cache` | JSONB 缓存表 | VOS API 缓存 | TTL 过期机制 |
| `sync_configs` | 普通表 | 同步任务配置 | Cron 表达式 |

### CDR 表优化（上亿级数据）

**复合主键**：`(start, flow_no)`
- 满足 TimescaleDB 分区要求
- `flow_no` 是 VOS 唯一标识（去重）

**自动分区**：
- 每 7 天一个分区（chunk）
- 自动创建、自动管理

**自动压缩**：
- 30 天后自动压缩（压缩比约 10:1）
- 不影响查询性能

**自动删除**：
- 1 年后自动删除（可配置）
- 释放存储空间

**性能优化**：
- 查询限制：最多 31 天范围
- 历史限制：不能查询 1 年前数据
- 强制分页：最大 100 条/页

---

## 🔧 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启某个服务
docker-compose restart backend

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

### 数据库管理

```bash
# 进入数据库容器
docker exec -it yk_vos_timescaledb psql -U vos_user -d vosadmin

# 备份数据库
docker exec yk_vos_timescaledb pg_dump -U vos_user -d vosadmin > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
docker exec -i yk_vos_timescaledb psql -U vos_user -d vosadmin < backup.sql

# 执行数据库迁移（进入 backend 容器后）
docker exec -it yk_vos_backend bash
alembic upgrade head
```

### 容器内操作

```bash
# 进入后端容器
docker exec -it yk_vos_backend bash

# 进入前端容器
docker exec -it yk_vos_frontend sh

# 创建新的数据库迁移
docker exec -it yk_vos_backend alembic revision --autogenerate -m "描述"

# 查看 Celery 任务队列
docker exec -it yk_vos_celery_worker celery -A app.tasks.celery_app inspect active
```

---

## 🐛 故障排查

### 后端启动失败

```bash
# 查看后端日志
docker-compose logs -f backend

# 常见问题：
# 1. 数据库连接失败 -> 检查 .env 中的 DATABASE_URL
# 2. 数据库迁移失败 -> 手动执行：docker exec -it yk_vos_backend alembic upgrade head
# 3. TimescaleDB 扩展未安装 -> 删除数据重新初始化
```

### 前端无法访问后端

```bash
# 检查前端环境变量
docker exec -it yk_vos_frontend env | grep NEXT_PUBLIC_API_BASE

# 应该显示：
# NEXT_PUBLIC_API_BASE=http://<服务器IP>:8000/api/v1

# 如果不对，手动修改 docker-compose.yaml 中的 NEXT_PUBLIC_API_BASE
# 然后重启前端：
docker-compose restart frontend
```

### 数据库空间不足

```bash
# 查看数据库大小
docker exec yk_vos_timescaledb psql -U vos_user -d vosadmin -c "\l+ vosadmin"

# 查看 CDR 表大小
docker exec yk_vos_timescaledb psql -U vos_user -d vosadmin -c "SELECT pg_size_pretty(pg_total_relation_size('cdrs'));"

# 手动触发压缩（如果自动压缩未生效）
docker exec yk_vos_timescaledb psql -U vos_user -d vosadmin -c "CALL run_job((SELECT job_id FROM timescaledb_information.jobs WHERE proc_name = 'policy_compression'));"

# 调整保留策略（例如改为 6 个月）
docker exec yk_vos_timescaledb psql -U vos_user -d vosadmin -c "SELECT remove_retention_policy('cdrs');"
docker exec yk_vos_timescaledb psql -U vos_user -d vosadmin -c "SELECT add_retention_policy('cdrs', INTERVAL '6 months');"
```

### Celery 任务不执行

```bash
# 查看 Celery Worker 日志
docker-compose logs -f celery-worker

# 查看 Celery Beat 日志
docker-compose logs -f celery-beat

# 检查任务队列
docker exec -it yk_vos_celery_worker celery -A app.tasks.celery_app inspect active
docker exec -it yk_vos_celery_worker celery -A app.tasks.celery_app inspect scheduled

# 重启 Celery 服务
docker-compose restart celery-worker celery-beat
```

---

## 📖 API 文档

启动服务后，访问以下地址查看完整 API 文档：

- **Swagger UI**：`http://<服务器IP>:8000/docs`
- **ReDoc**：`http://<服务器IP>:8000/redoc`

主要 API 端点：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/vos/instances` | GET | 获取 VOS 节点列表 |
| `/api/v1/vos/customers/summary` | GET | 获取客户统计 |
| `/api/v1/cdr/query-from-vos/{instance_id}` | POST | 查询历史话单（智能查询） |
| `/api/v1/tasks/status` | GET | 获取任务队列状态 |
| `/api/v1/vos-api/{api_name}` | POST | 调用 VOS API |

---

## 🔒 安全建议

### 生产环境部署

1. **修改默认密码**
   - 管理员账户：首次登录后立即修改
   - 数据库密码：修改 `.env` 中的 `POSTGRES_PASSWORD`
   - JWT 密钥：修改 `.env` 中的 `SECRET_KEY`

2. **配置防火墙**
   ```bash
   # 只开放必要端口
   ufw allow 22/tcp    # SSH
   ufw allow 3000/tcp  # 前端
   ufw allow 8000/tcp  # 后端
   ufw enable
   ```

3. **启用 HTTPS**
   - 使用 Nginx 反向代理
   - 配置 SSL 证书（Let's Encrypt）

4. **限制数据库访问**
   - 不要将 5430 端口暴露到公网
   - 使用 Docker 内部网络通信

5. **定期备份**
   - 每天自动备份数据库
   - 保留至少 7 天的备份

---

## 📈 性能基准

### 话单查询性能（百万级数据）

| 查询方式 | 响应时间 | 数据来源 |
|---------|---------|---------|
| 本地数据库（有索引） | < 10ms | TimescaleDB |
| 本地数据库（无索引） | 100-500ms | TimescaleDB |
| VOS API | 2-5s | VOS3000 |

### 并发性能

- **后端**：支持 1000+ 并发连接（FastAPI + Uvicorn）
- **数据库**：支持 100+ 并发查询（TimescaleDB）
- **前端**：支持 500+ 并发访问（Next.js）

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

开发环境搭建：

```bash
# 后端开发
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端开发
cd frontend
npm install
npm run dev
```

---

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](./LICENSE) 文件。

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Next.js](https://nextjs.org/) - React 生产级框架
- [TimescaleDB](https://www.timescale.com/) - 时序数据库
- [Celery](https://docs.celeryproject.org/) - 分布式任务队列

---

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- **项目主页**：<your-repo-url>
- **Issues**：<your-repo-url>/issues
- **Email**：your-email@example.com

---

**Made with ❤️ by YK-VOS Team**
