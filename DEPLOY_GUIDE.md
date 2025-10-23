# YK-VOS 部署指南

> 🐧 **系统要求**：Debian 10+ 或 Ubuntu 20.04+

## 🚀 快速部署

### 全新服务器部署

```bash
# 1. 克隆代码
git clone <your-repo-url>
cd yk-vos

# 2. 运行初始化脚本
chmod +x init-deploy.sh
./init-deploy.sh
```

脚本会自动完成：
- ✅ 检查系统环境（Debian/Ubuntu）
- ✅ 安装依赖（如需要）
- ✅ 创建配置文件
- ✅ 构建基础镜像
- ✅ 启动所有服务
- ✅ 初始化数据库
- ✅ 验证部署

---

## 📋 手动部署步骤

如果需要手动部署或了解细节：

### 1. 环境检查

```bash
# 检查 Docker
docker --version

# 检查 Docker Compose
docker-compose --version

# 检查 Docker 运行状态
docker info
```

### 2. 创建配置文件

**backend/.env**：
```bash
POSTGRES_USER=vos_user
POSTGRES_PASSWORD=your_strong_password
POSTGRES_DB=vosadmin
DATABASE_URL=postgresql://vos_user:your_strong_password@postgres:5432/vosadmin
SECRET_KEY=$(openssl rand -hex 32)
REDIS_URL=redis://redis:6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

**frontend/.env.local**：
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 构建基础镜像

```bash
# 构建后端和前端基础镜像（只需一次）
docker-compose -f docker-compose.base.yaml build
```

### 4. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

### 5. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 检查后端健康
curl http://localhost:8000/health

# 检查前端
curl http://localhost:3000
```

---

## 🔄 日常操作

### 修改代码

代码通过挂载映射，修改后自动重载：

```bash
# 1. 编辑代码
vim backend/app/xxx.py

# 2. 查看日志（自动重载）
docker-compose logs -f backend

# 3. 测试
# 刷新浏览器或重新调用 API
```

### 更新代码

```bash
# 拉取最新代码
git pull

# 重启服务（代码挂载会自动更新）
docker-compose restart
```

### 更新依赖

```bash
# 修改 requirements.txt 或 package.json 后

# 重新构建基础镜像
docker-compose -f docker-compose.base.yaml build

# 重启服务
docker-compose restart
```

---

## 📊 架构说明

### 文件结构

```
yk-vos/
├── docker-compose.base.yaml    # 基础镜像构建
├── docker-compose.yaml         # 服务编排（挂载代码）
├── data/                       # 数据目录（Git 忽略）
│   └── postgres/              # PostgreSQL 数据（本地映射）
├── backend/
│   ├── Dockerfile.base         # 后端基础镜像
│   ├── Dockerfile             # 完整构建（可选）
│   └── ...                     # 代码（挂载）
└── frontend/
    ├── Dockerfile.base         # 前端基础镜像
    ├── Dockerfile             # 完整构建（可选）
    └── ...                     # 代码（挂载）
```

### 部署原理

```
基础镜像（Dockerfile.base）
   ├─> 系统依赖
   ├─> Python/Node 包
   └─> 不包含代码

Docker Compose（docker-compose.yaml）
   ├─> 使用基础镜像
   ├─> 挂载代码目录
   └─> 启动服务
```

### 优势

- ⚡ **快速部署**：修改代码后重启容器即可（< 3秒）
- 💾 **节省空间**：基础镜像只需构建一次
- 🔄 **自动重载**：后端和前端都支持热重载

---

## 🔧 故障排查

### 问题 1：端口被占用

```bash
# 查看端口占用
netstat -tlnp | grep -E '3000|8000|5432|6379'

# 修改端口
# 编辑 docker-compose.yaml
ports:
  - "3001:3000"  # 改为其他端口
```

### 问题 2：数据库连接失败

```bash
# 检查数据库容器
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 进入数据库容器
docker-compose exec postgres bash
```

### 问题 3：代码修改不生效

```bash
# 检查卷挂载
docker-compose exec backend ls -la /srv

# 重启服务
docker-compose restart backend frontend

# 清理并重启
docker-compose down && docker-compose up -d
```

---

## 🔐 安全建议

### 生产环境配置

1. **修改默认密码**
   ```bash
   # 修改 backend/.env 中的数据库密码
   POSTGRES_PASSWORD=your_very_strong_password
   ```

2. **使用强密钥**
   ```bash
   # 生成新的 SECRET_KEY
   SECRET_KEY=$(openssl rand -hex 32)
   ```

3. **配置防火墙**
   ```bash
   # 只允许必要的端口
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw enable
   ```

4. **使用 HTTPS**
   - 配置 Nginx 反向代理
   - 使用 Let's Encrypt 证书

---

## 📚 相关文档

- [README.md](./README.md) - 项目说明
- [UPGRADE_GUIDE.md](./UPGRADE_GUIDE.md) - 升级指南

---

**部署完成后，访问 http://localhost:3000 开始使用！** 🎉

