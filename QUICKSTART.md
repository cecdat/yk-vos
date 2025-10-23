# YK-VOS 快速开始

> 🐧 **系统要求**：Debian 10+ 或 Ubuntu 20.04+

## 🚀 全新服务器部署

```bash
# 1. 克隆代码
git clone <your-repo-url>
cd yk-vos

# 2. 运行一键部署脚本
chmod +x init-deploy.sh
./init-deploy.sh
```

**脚本会自动完成**：
- ✅ 检查系统环境（Debian/Ubuntu）
- ✅ 检查 Docker 和 Docker Compose
- ✅ 创建环境配置文件（.env）
- ✅ 构建基础镜像（依赖）
- ✅ 启动所有服务
- ✅ 初始化数据库
- ✅ 验证部署结果

**预计时间**：首次约 5-10 分钟

---

## 🎯 部署成功后

### 访问地址
- 前端界面：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 默认账号
- 用户名：`admin`
- 密码：`admin123`

⚠️ **首次登录后请立即修改密码！**

---

## 🔧 日常使用

### 修改代码
```bash
# 1. 编辑代码文件
vim backend/app/xxx.py

# 2. 代码自动重载（< 3秒）
# 无需任何操作！

# 3. 刷新浏览器测试
```

### 查看日志
```bash
# 所有服务
docker-compose logs -f

# 只看后端
docker-compose logs -f backend

# 只看前端
docker-compose logs -f frontend
```

### 重启服务
```bash
# 单个服务
docker-compose restart backend

# 所有服务
docker-compose restart
```

### 停止服务
```bash
# 停止（保留数据）
docker-compose down

# 停止并删除数据（慎用）
docker-compose down -v
```

---

## 🔄 更新代码

```bash
# 拉取最新代码
git pull

# 重启服务
docker-compose restart
```

---

## 📦 更新依赖

如果修改了 `requirements.txt` 或 `package.json`：

```bash
# 重新构建基础镜像
docker-compose -f docker-compose.base.yaml build

# 重启服务
docker-compose restart
```

---

## 🆘 遇到问题？

### 1. 检查服务状态
```bash
docker-compose ps
```

### 2. 查看日志
```bash
docker-compose logs -f
```

### 3. 完全重启
```bash
docker-compose down
docker-compose up -d
```

### 4. 查看详细文档
- [README.md](./README.md) - 完整使用指南
- [UPGRADE_GUIDE.md](./UPGRADE_GUIDE.md) - 升级指南
- [DEPLOY_GUIDE.md](./DEPLOY_GUIDE.md) - 详细部署说明

---

## 💾 数据备份

### PostgreSQL 数据位置
- **本地路径**：`./data/postgres`
- **容器路径**：`/var/lib/postgresql/data`

### 快速备份
```bash
# 方式一：复制数据目录（需停止服务）
docker-compose down
tar -czf backup-$(date +%Y%m%d).tar.gz data/
docker-compose up -d

# 方式二：使用 pg_dump（推荐，无需停服）
docker-compose exec postgres pg_dump -U vos_user vos_db > backup.sql
```

### 恢复数据
```bash
# 从备份恢复
docker-compose exec -T postgres psql -U vos_user vos_db < backup.sql
```

---

**开始使用 YK-VOS！** 🎉

