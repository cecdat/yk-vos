# YK-VOS - VOS3000 管理与分析平台

一个现代化的 VOS3000 管理和分析平台，提供实时监控、历史话单查询和智能数据分析功能。

## ✨ 核心特性

- 📊 **实时监控**: VOS实例健康状态、在线话机、网关状态
- 📞 **话单查询**: 历史CDR数据查询和导出（支持亿级数据）
- 👥 **客户管理**: 账户信息、自动同步
- 🔄 **智能查询**: 本地数据库 → VOS API 智能切换
- 🗄️ **双数据库架构**: PostgreSQL (配置) + ClickHouse (话单)
- 🐳 **容器化部署**: Docker Compose 一键部署

## 🏗️ 技术栈

**后端**: FastAPI + SQLAlchemy + ClickHouse + PostgreSQL + Redis + Celery

**前端**: Next.js 14 + React + Tailwind CSS + TypeScript

## 🚀 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 内存 4GB+
- 磁盘 20GB+

### 一键部署

```bash
# 拉取代码
git clone <your-repo-url>
cd yk-vos

# 执行部署脚本
bash deploy.sh
```

部署脚本会自动完成：
1. 创建数据目录并设置权限
2. 生成配置文件
3. 构建Docker镜像
4. 启动所有服务
5. 等待服务就绪

### 访问系统

- **前端**: http://服务器IP:3000
- **后端API**: http://服务器IP:8000
- **默认账号**: admin / admin123

### 数据库账号

- **用户名**: vosadmin
- **密码**: Ykxx@2025

## 📂 项目结构

```
yk-vos/
├── backend/              # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── alembic/     # 数据库迁移
│   │   ├── core/        # 核心模块
│   │   ├── models/      # 数据模型
│   │   ├── routers/     # API路由
│   │   └── tasks/       # Celery任务
│   └── requirements.txt
│
├── frontend/             # 前端服务 (Next.js)
│   ├── app/             # 页面和路由
│   ├── components/      # React组件
│   └── package.json
│
├── clickhouse/           # ClickHouse初始化脚本
│   └── init/
│       └── 01_create_tables.sql
│
├── data/                 # 数据持久化目录
│   ├── postgres/        # PostgreSQL数据
│   └── clickhouse/      # ClickHouse数据
│
├── docker-compose.yaml   # 服务编排配置
├── docker-compose.base.yaml  # 基础镜像构建
├── init-deploy.sh        # 初始化部署脚本
└── deploy.sh             # 日常部署脚本
```

## 🗄️ 数据库架构

**PostgreSQL**: 配置数据
- 用户管理 (users)
- VOS实例配置 (vos_instances)
- 健康检查记录 (vos_health_checks)
- 客户管理 (customers)
- 同步配置 (sync_configs)

**ClickHouse**: 话单数据
- CDR记录 (cdrs)
- 按月自动分区
- 自动去重
- 物化视图统计

## 📊 数据同步

系统通过Celery后台任务自动同步VOS数据：

- **客户数据**: 每2分钟同步一次
- **话机状态**: 每2分钟同步一次
- **VOS健康检查**: 每5分钟检查一次
- **通用API数据**: 每1分钟同步一次

## 🔧 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [service_name]

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 备份数据库
docker exec yk_vos_postgres pg_dump -U vosadmin vosadmin > backup.sql

# 备份ClickHouse
docker exec yk_vos_clickhouse clickhouse-client --query "SELECT * FROM vos_cdrs.cdrs FORMAT TabSeparated" > backup_cdrs.tsv
```

## 🐛 故障排查

### 查看服务日志

```bash
docker-compose logs postgres
docker-compose logs clickhouse
docker-compose logs backend
docker-compose logs frontend
```

### 数据库连接问题

检查容器是否正常运行：
```bash
docker-compose ps
```

检查数据库是否就绪：
```bash
# PostgreSQL
docker-compose exec postgres pg_isready -U vosadmin

# ClickHouse
docker-compose exec clickhouse clickhouse-client --query "SELECT 1"
```

### 重新部署

如果遇到问题，可以完全重新部署：

```bash
# 停止并删除所有容器
docker-compose down -v

# 清理数据（⚠️ 会删除所有数据）
sudo rm -rf data/postgres/* data/clickhouse/*

# 重新设置权限
sudo chown -R 999:999 data/postgres
sudo chown -R 101:101 data/clickhouse

# 重新部署
bash deploy.sh
```

## 🔒 安全建议

1. **首次登录后立即修改管理员密码**
2. **配置防火墙，只开放必要端口**
3. **使用Nginx反向代理并配置HTTPS**
4. **定期备份数据库**

## 📖 API 文档

启动服务后访问：

- **Swagger UI**: http://服务器IP:8000/docs
- **ReDoc**: http://服务器IP:8000/redoc

## 📄 许可证

MIT License

---

**Made with ❤️ by YK-VOS Team**
