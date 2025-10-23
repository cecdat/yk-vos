# 部署脚本使用指南

YK-VOS 提供了多个部署脚本，适用于不同场景。

## 📋 脚本概览

| 脚本 | 适用场景 | 备份数据 | 数据库迁移 | 使用时机 |
|-----|---------|---------|-----------|----------|
| `init-deploy.sh` | 全新服务器部署 | ❌ | ✅ | 首次部署 |
| `quick-update.sh` | 日常代码更新 | ❌ | ❌ | 修改代码后 |
| `upgrade.sh` | 完整升级 | ✅ | ✅ | 重要更新 |
| `deploy.sh` | 交互式部署工具 | 可选 | 可选 | 任何时候 |

---

## 🚀 init-deploy.sh - 全新服务器初始化

**适用场景**：第一次在新服务器上部署

### 功能
- ✅ 检查系统环境（Debian/Ubuntu）
- ✅ 检查 Docker 和 Docker Compose
- ✅ 创建环境配置文件
- ✅ 构建基础镜像
- ✅ 启动所有服务
- ✅ 初始化数据库
- ✅ 验证部署结果

### 使用方法
```bash
chmod +x init-deploy.sh
./init-deploy.sh
```

### 预计时间
- 首次部署：5-10 分钟
- 主要耗时：基础镜像构建

---

## ⚡ quick-update.sh - 快速更新（推荐日常使用）

**适用场景**：修改了代码文件，需要快速部署

### 功能
- ✅ 拉取最新代码（git pull）
- ✅ 重启相关服务（backend, frontend, celery）
- ✅ 健康检查

### 使用方法
```bash
bash quick-update.sh
```

### 优点
- 🚀 快速（< 30 秒）
- 💾 不停止数据库
- 🔄 自动重启应用服务

### 何时使用
- 修改了 Python 代码
- 修改了 React/TypeScript 代码
- 修改了配置文件
- 日常开发迭代

### 何时不用
- ❌ 修改了依赖（requirements.txt, package.json）
- ❌ 有新的数据库迁移
- ❌ 修改了 Docker 配置

---

## 🔄 upgrade.sh - 完整升级

**适用场景**：重要更新、有数据库变更、依赖更新

### 功能
- ✅ 备份数据库（自动）
- ✅ 拉取最新代码
- ✅ 检查未提交的更改
- ✅ 停止服务
- ✅ 构建镜像
- ✅ 执行数据库迁移
- ✅ 启动服务
- ✅ 验证部署

### 使用方法
```bash
bash upgrade.sh
```

### 优点
- 💾 自动备份数据库
- 🔒 安全可靠
- 📊 详细的验证报告

### 何时使用
- 有新的数据库迁移脚本
- 更新了依赖包
- 重要版本升级
- 需要备份数据库

### 预计时间
- 2-5 分钟（取决于数据库大小和代码变更）

---

## 🎛️ deploy.sh - 一键部署工具（交互式）

**适用场景**：不确定用哪个脚本，或需要执行多种操作

### 功能菜单

```
1) 快速更新 (拉代码 + 重启服务)
2) 完整升级 (备份 + 拉代码 + 迁移 + 重启)
3) 仅重启服务
4) 查看服务状态
5) 查看日志
0) 退出
```

### 使用方法
```bash
bash deploy.sh
```

### 优点
- 🎯 交互式菜单，简单直观
- 🔧 集成多种常用操作
- 📊 实时显示服务状态
- 📝 方便查看日志

### 适合人群
- 不熟悉命令行的用户
- 需要执行多种操作
- 调试和排查问题

---

## 📊 场景选择指南

### 场景 1：修改了一个 Python 文件
```bash
bash quick-update.sh
```
✅ 最快，30 秒完成

### 场景 2：添加了新的依赖包
```bash
bash upgrade.sh
```
✅ 需要重新构建镜像

### 场景 3：有新的数据库迁移
```bash
bash upgrade.sh
```
✅ 自动备份数据库，执行迁移

### 场景 4：全新服务器
```bash
./init-deploy.sh
```
✅ 一键完成所有初始化

### 场景 5：不确定用哪个
```bash
bash deploy.sh
```
✅ 菜单式选择

### 场景 6：查看服务状态
```bash
bash deploy.sh
# 选择 4) 查看服务状态
```

### 场景 7：快速查看日志
```bash
bash deploy.sh
# 选择 5) 查看日志
```

---

## 🔧 手动操作（高级用户）

如果你熟悉 Docker 命令，也可以手动操作：

### 快速重启
```bash
git pull
docker-compose restart backend frontend
```

### 只重启后端
```bash
docker-compose restart backend celery-worker celery-beat
```

### 重新构建并启动
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### 查看日志
```bash
# 所有服务
docker-compose logs -f

# 只看后端
docker-compose logs -f backend

# 最后 100 行
docker-compose logs --tail=100 backend
```

---

## ⚠️ 注意事项

### 1. 备份数据库
- `quick-update.sh` **不备份**数据库
- `upgrade.sh` **自动备份**数据库到 `backups/` 目录
- 重要操作前建议手动备份：
  ```bash
  docker-compose exec postgres pg_dump -U vos_user vosadmin > backup.sql
  ```

### 2. 服务停机时间
- `quick-update.sh`：约 5-10 秒（重启服务）
- `upgrade.sh`：约 30-60 秒（完全重启）
- `init-deploy.sh`：全新部署，无停机时间

### 3. 数据持久化
- 所有脚本都保留 `./data/postgres` 数据
- 只有 `docker-compose down -v` 会删除数据

### 4. 错误处理
- 所有脚本都有 `set -e`，遇到错误自动退出
- 查看详细错误：`docker-compose logs`

---

## 🆘 故障排查

### 问题 1：脚本无法执行
```bash
chmod +x *.sh
```

### 问题 2：端口被占用
修改 `docker-compose.yaml` 中的端口映射

### 问题 3：数据库迁移失败
```bash
# 手动执行迁移
docker-compose exec backend bash -c "cd /srv/app && alembic upgrade head"
```

### 问题 4：服务启动失败
```bash
# 查看详细日志
docker-compose logs -f backend

# 完全重启
docker-compose down
docker-compose up -d
```

---

## 📝 最佳实践

1. **日常开发**：使用 `quick-update.sh`
2. **重要更新**：使用 `upgrade.sh`
3. **不确定时**：使用 `deploy.sh` 菜单
4. **定期备份**：手动或通过 `upgrade.sh`
5. **查看日志**：先用 `deploy.sh` 菜单，再用 `docker-compose logs`

---

**选择合适的脚本，高效部署！** 🚀

