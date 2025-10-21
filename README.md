# YK-VOS v4 - VOS3000 查询与分析平台

一个现代化的 VOS3000 管理和分析平台，提供话机监控、历史话单查询和数据分析功能。

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11-green.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)

## ✨ 特性

- 🎨 **现代化 UI** - 使用 Next.js + Tailwind CSS 构建的响应式界面
- 🔐 **安全认证** - JWT Token 认证机制
- 📊 **实时监控** - 在线话机状态实时同步
- 📞 **话单查询** - 历史 CDR 数据查询和分析
- 🔄 **自动同步** - Celery 定时任务自动同步数据
- 🐳 **容器化部署** - Docker Compose 一键部署
- 📈 **数据可视化** - 基于 Recharts 的图表展示

## 🏗️ 技术栈

### 后端
- **FastAPI** - 现代、高性能的 Python Web 框架
- **SQLAlchemy** - ORM 数据库操作
- **PostgreSQL** - 主数据库
- **Redis** - 缓存和消息队列
- **Celery** - 分布式任务队列
- **Alembic** - 数据库迁移工具

### 前端
- **Next.js 14** - React 框架
- **Tailwind CSS** - 实用优先的 CSS 框架
- **Recharts** - 数据可视化
- **Axios** - HTTP 客户端

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose
- 2GB+ RAM
- 开放端口：3000（前端）、8000（后端）

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd yk-vos
```

### 2. 配置环境变量

#### 方式一：使用自动脚本（推荐）

**Linux/Mac:**
```bash
chmod +x setup_env.sh
./setup_env.sh
```

**Windows PowerShell:**
```powershell
.\setup_env.ps1
```

#### 方式二：手动配置

参考 [ENV_SETUP.md](./ENV_SETUP.md) 手动创建配置文件。

### 3. 启动服务

```bash
docker-compose up --build -d
```

### 4. 访问应用

- 🌐 **前端界面**: http://localhost:3000
- 📚 **API 文档**: http://localhost:8000/docs
- ❤️ **健康检查**: http://localhost:8000/health

### 5. 登录系统

**默认管理员账号：**
- 用户名：`admin`
- 密码：`Ykxx@2025`

> ⚠️ **重要**：首次登录后请立即修改默认密码！

## 📖 文档

- [完整部署指南](./SETUP_GUIDE.md) - 详细的部署和配置说明
- [环境变量配置](./ENV_SETUP.md) - 环境变量配置详解
- [API 文档](http://localhost:8000/docs) - 交互式 API 文档（启动服务后访问）

## 🔧 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 进入后端容器
docker exec -it yk_vos_backend /bin/sh

# 手动执行数据库迁移
docker exec -it yk_vos_backend alembic upgrade head
```

## 📊 自动任务

系统包含以下自动执行的定时任务：

| 任务 | 执行频率 | 说明 |
|------|---------|------|
| 同步在线话机 | 每 5 分钟 | 从 VOS 实例获取在线话机列表 |
| 同步 CDR 话单 | 每天 01:30 | 同步前一天的话单数据 |

## 🏛️ 项目结构

```
yk-vos/
├── backend/                # 后端服务
│   ├── app/
│   │   ├── core/          # 核心模块（配置、数据库）
│   │   ├── models/        # 数据模型
│   │   ├── routers/       # API 路由
│   │   ├── schemas/       # Pydantic 模式
│   │   └── tasks/         # Celery 任务
│   ├── alembic/           # 数据库迁移
│   └── scripts/           # 初始化脚本
├── frontend/              # 前端应用
│   ├── app/               # Next.js 页面
│   ├── components/        # React 组件
│   └── lib/               # 工具库
├── docker-compose.yml     # Docker 编排配置
├── SETUP_GUIDE.md        # 部署指南
└── ENV_SETUP.md          # 环境变量配置
```

## 🔐 安全建议

1. ✅ 修改默认管理员密码
2. ✅ 更新 `backend/.env` 中的 `SECRET_KEY`
3. ✅ 使用强密码保护数据库
4. ✅ 在生产环境中配置 HTTPS
5. ✅ 限制 CORS 允许的来源

详细安全配置请参考 [SETUP_GUIDE.md](./SETUP_GUIDE.md)。

## 🐛 故障排查

遇到问题？查看 [SETUP_GUIDE.md](./SETUP_GUIDE.md) 中的故障排查章节。

常见问题：
- 前端无法连接后端 → 检查 API 地址配置
- 数据库连接失败 → 检查数据库容器状态
- Celery 任务不执行 → 检查 Redis 连接
- 端口冲突 → 修改 docker-compose.yml 中的端口映射

## 📝 开发指南

### 本地开发

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

### 数据库迁移

```bash
# 生成新的迁移文件
docker exec -it yk_vos_backend alembic revision --autogenerate -m "description"

# 应用迁移
docker exec -it yk_vos_backend alembic upgrade head

# 回滚迁移
docker exec -it yk_vos_backend alembic downgrade -1
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- FastAPI - 优秀的 Python Web 框架
- Next.js - 强大的 React 框架
- VOS3000 - 通信平台

---

**有问题？** 查看 [完整文档](./SETUP_GUIDE.md) 或提交 Issue。

**祝您使用愉快！** 🎉
