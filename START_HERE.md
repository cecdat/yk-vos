# 🚀 从这里开始 - YK-VOS v4

欢迎使用 YK-VOS v4！本文档将帮助您快速启动项目。

## ⚡ 5 分钟快速启动

### 方式一：自动脚本（最简单）

#### Windows 用户：
```powershell
# 右键以管理员身份运行 PowerShell
.\quick_start.ps1
```

#### Linux/Mac 用户：
```bash
chmod +x quick_start.sh
./quick_start.sh
```

### 方式二：手动启动

#### 步骤 1：配置环境变量

**Windows:**
```powershell
.\setup_env.ps1
```

**Linux/Mac:**
```bash
chmod +x setup_env.sh
./setup_env.sh
```

#### 步骤 2：启动服务
```bash
docker-compose up --build -d
```

#### 步骤 3：等待服务启动（约 30 秒）
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 🌐 访问地址

启动成功后，访问以下地址：

- **前端界面**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 🔑 登录信息

```
用户名: admin
密码: Ykxx@2025
```

⚠️ **重要**: 首次登录后请立即修改密码！

## 📚 文档导航

| 文档 | 说明 | 适用场景 |
|------|------|---------|
| [README.md](./README.md) | 项目概述和快速开始 | 了解项目 |
| [SETUP_GUIDE.md](./SETUP_GUIDE.md) | 详细部署和运维指南 | 生产环境部署 |
| [ENV_SETUP.md](./ENV_SETUP.md) | 环境变量配置详解 | 自定义配置 |
| [PROJECT_COMPLETION.md](./PROJECT_COMPLETION.md) | 项目完成报告 | 了解项目结构 |
| [CHANGELOG.md](./CHANGELOG.md) | 更新日志 | 了解版本变更 |

## ✅ 启动后检查清单

- [ ] 所有 6 个容器都在运行
- [ ] 前端界面可以访问 (http://localhost:3000)
- [ ] API 文档可以访问 (http://localhost:8000/docs)
- [ ] 可以使用默认账号登录
- [ ] 能看到演示 VOS 实例

## 🔧 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看所有日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 重启服务
docker-compose restart

# 停止服务
docker-compose stop

# 完全停止并删除容器
docker-compose down

# 进入后端容器
docker exec -it yk_vos_backend /bin/sh

# 查看数据库
docker exec -it yk_vos_postgres psql -U vos -d vosdb
```

## 🐛 遇到问题？

### 问题 1: 端口被占用
**症状**: 启动时提示端口冲突

**解决方案**: 修改 `docker-compose.yml` 中的端口映射
```yaml
ports:
  - "8001:8000"  # 将 8000 改为 8001
  - "3001:3000"  # 将 3000 改为 3001
```

### 问题 2: 前端无法连接后端
**症状**: 前端界面空白或显示连接错误

**解决方案**: 检查 `frontend/.env` 中的 API 地址
```env
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
```

### 问题 3: 容器启动失败
**症状**: `docker-compose ps` 显示容器退出

**解决方案**:
```bash
# 查看具体错误
docker-compose logs [服务名]

# 常见原因：
# 1. 环境变量未配置 - 运行 setup_env 脚本
# 2. 端口被占用 - 修改端口映射
# 3. Docker 内存不足 - 增加 Docker 内存限制
```

### 问题 4: 数据库连接失败
**症状**: 后端日志显示数据库连接错误

**解决方案**:
```bash
# 检查数据库容器状态
docker-compose ps db

# 查看数据库日志
docker-compose logs db

# 重启数据库
docker-compose restart db
```

## 📞 获取帮助

1. 查看 [SETUP_GUIDE.md](./SETUP_GUIDE.md) 的故障排查章节
2. 检查容器日志: `docker-compose logs -f`
3. 查看 API 文档: http://localhost:8000/docs
4. 提交 Issue（如果使用 Git）

## 🎯 下一步

启动成功后，您可以：

1. **浏览界面**
   - 访问仪表盘
   - 查看 VOS 实例列表
   - 浏览历史话单

2. **添加 VOS 实例**
   - 使用 API 或数据库添加新的 VOS 节点
   - 配置实例的连接信息

3. **监控数据同步**
   - 查看 Celery 日志: `docker-compose logs -f celery`
   - 验证定时任务执行

4. **自定义配置**
   - 修改同步频率（编辑 `app/tasks/celery_app.py`）
   - 调整前端样式
   - 添加自定义功能

## 🔐 生产环境部署

如果要部署到生产环境，请务必：

1. ✅ 修改 `backend/.env` 中的 `SECRET_KEY`
```bash
# 生成随机密钥
openssl rand -hex 32
```

2. ✅ 修改数据库密码
```yaml
# docker-compose.yml
environment:
  POSTGRES_PASSWORD: your-secure-password
```

3. ✅ 修改管理员密码
   - 登录后在系统中修改
   - 或修改 `scripts/init_admin.py`

4. ✅ 配置 HTTPS
   - 使用 Nginx 反向代理
   - 申请 SSL 证书

5. ✅ 设置防火墙
```bash
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

详细说明请参考 [SETUP_GUIDE.md](./SETUP_GUIDE.md)。

## 📊 系统架构

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ↓
┌─────────────┐      ┌──────────────┐
│  Frontend   │ ←──→ │   Backend    │
│  (Next.js)  │      │   (FastAPI)  │
└─────────────┘      └───────┬──────┘
                             │
                ┌────────────┼────────────┐
                ↓            ↓            ↓
         ┌──────────┐  ┌─────────┐  ┌─────────┐
         │PostgreSQL│  │  Redis  │  │ Celery  │
         └──────────┘  └─────────┘  └─────────┘
                                          │
                                          ↓
                                   ┌─────────────┐
                                   │ VOS3000 API │
                                   └─────────────┘
```

## 🎉 开始使用

现在您已经准备好了！运行启动脚本或按照手动步骤，几分钟后就能看到系统运行。

**祝您使用愉快！** 🚀

---

**需要帮助？** 查看 [SETUP_GUIDE.md](./SETUP_GUIDE.md) 或 [README.md](./README.md)

