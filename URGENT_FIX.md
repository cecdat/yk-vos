# 紧急修复指南

## 🚨 当前问题

1. ✅ **Celery 时间比较错误** - 已修复
2. ❌ **customers 表不存在** - 需要运行迁移

---

## 🚀 快速修复（3 步搞定）

### 步骤 1: 拉取最新代码

```bash
cd /data/yk-vos
git pull
```

**预期输出**：
```
remote: Enumerating objects: ...
Receiving objects: 100% ...
Updating 445e6cf..3110e28
```

---

### 步骤 2: 运行数据库迁移

```bash
# 方法 A: 使用迁移脚本（推荐）
chmod +x run-migration.sh
./run-migration.sh
```

**或者手动执行**：
```bash
# 方法 B: 手动运行迁移
docker-compose exec backend bash -c "cd /srv/app && alembic upgrade head"
```

**预期输出**：
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 0006 -> 0007, add customers table
```

---

### 步骤 3: 重启服务

```bash
docker-compose restart backend celery-worker celery-beat
```

**等待 10 秒，然后验证**：
```bash
# 查看容器状态（应该都是 Up）
docker-compose ps

# 查看后端日志（不应该有错误）
docker-compose logs --tail=20 backend

# 查看 Celery 日志（不应该有错误）
docker-compose logs --tail=20 celery-worker
```

---

## ✅ 验证修复

### 1. 检查数据库表

```bash
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt"
```

**应该看到 customers 表**：
```
 Schema |      Name       | Type  |  Owner   
--------+-----------------+-------+----------
 ...
 public | customers       | table | vos_user  ← 应该存在
 ...
```

### 2. 检查 Alembic 版本

```bash
docker-compose exec backend bash -c "cd /srv/app && alembic current"
```

**应该显示**：
```
0007_add_customers_table (head)
```

### 3. 测试客户管理功能

1. 打开浏览器：`http://YOUR_SERVER_IP:3000`
2. 登录（admin/admin123）
3. 点击"客户管理"
4. **应该能看到客户列表**（或者显示"暂无客户数据"）
5. **不应该出现 500 错误**

### 4. 检查 Celery 任务

```bash
# 查看 Celery worker 日志，不应该有时间比较错误
docker-compose logs --tail=50 celery-worker | grep -i error
```

**如果没有输出或只有旧的错误，说明修复成功。**

---

## 🐛 如果还有问题

### 问题 A: 迁移失败

```bash
# 查看详细错误
docker-compose logs backend | grep -i "alembic\|migration\|error"

# 检查 Alembic 配置
docker-compose exec backend bash -c "cd /srv/app && ls -la alembic.ini"

# 检查迁移文件
docker-compose exec backend bash -c "ls -la /srv/app/alembic/versions/"
```

**应该看到 0007_add_customers_table.py**

### 问题 B: customers 表仍然不存在

```bash
# 手动进入容器执行迁移
docker-compose exec backend bash
cd /srv/app
alembic current
alembic upgrade head
exit

# 验证
docker-compose exec postgres psql -U vos_user -d vosadmin -c "SELECT COUNT(*) FROM customers;"
```

### 问题 C: Celery 仍然报错

```bash
# 重新构建并重启
docker-compose down
docker-compose -f docker-compose.base.yaml build --no-cache backend-base
docker-compose up -d

# 查看日志
docker-compose logs -f celery-worker
```

---

## 📊 完整诊断命令

运行这个脚本获取完整的系统状态：

```bash
cat > diagnose.sh << 'EOF'
#!/bin/bash
echo "========================================
🔍 YK-VOS 系统诊断
========================================"
echo ""

echo "1️⃣  容器状态"
docker-compose ps
echo ""

echo "2️⃣  数据库表"
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt" | grep customers
echo ""

echo "3️⃣  Alembic 版本"
docker-compose exec backend bash -c "cd /srv/app && alembic current"
echo ""

echo "4️⃣  后端日志（最近 20 行）"
docker-compose logs --tail=20 backend | grep -i "error\|customers"
echo ""

echo "5️⃣  Celery 日志（最近 20 行）"
docker-compose logs --tail=20 celery-worker | grep -i "error\|timezone"
echo ""

echo "✅ 诊断完成"
EOF

chmod +x diagnose.sh
./diagnose.sh
```

把输出结果发给我，我会帮你分析。

---

## 📝 已修复的问题

### 提交记录

```
提交 1: 6cc2925 - 添加 customers 表的数据库迁移
  - 创建 0007_add_customers_table.py
  - 创建 run-migration.sh

提交 2: 3110e28 - 修复 Celery 时间比较错误
  - 修复 vos_data_cache.py 中的 is_expired() 方法
  - 使用 timezone-aware datetime
```

### 修复内容

1. ✅ **数据库迁移**：添加 customers 表
2. ✅ **时间比较**：修复 offset-naive 和 offset-aware datetime 比较错误
3. ✅ **迁移脚本**：提供自动化迁移工具

---

## 🎯 关键文件

- `backend/app/alembic/versions/0007_add_customers_table.py` - 迁移文件
- `backend/app/models/vos_data_cache.py` - 修复的时间比较
- `run-migration.sh` - 迁移辅助脚本

---

## 💡 预防措施

**每次拉取代码后**，运行以下命令确保数据库是最新的：

```bash
# 快速检查并更新
docker-compose exec backend bash -c "cd /srv/app && alembic current && alembic upgrade head"
```

**或者添加到自动化脚本**：

```bash
# 添加到 quick-update.sh
echo "检查数据库迁移..."
docker-compose exec backend bash -c "cd /srv/app && alembic upgrade head"
```

---

## 🆘 紧急联系

如果上述步骤都无法解决问题：

1. 停止所有服务：`docker-compose down`
2. 备份数据库：`docker-compose exec postgres pg_dump -U vos_user vosadmin > backup.sql`
3. 清除数据重新部署：`rm -rf data/postgres && ./init-deploy.sh`
4. 恢复数据：`docker-compose exec -T postgres psql -U vos_user -d vosadmin < backup.sql`

---

## ✨ 修复后的效果

修复成功后，你应该能够：

- ✅ 正常访问客户管理页面
- ✅ 看到客户列表（如果有数据）
- ✅ Celery 任务正常运行，无错误日志
- ✅ 系统整体稳定运行

---

**现在请按照上述步骤操作，有问题随时告诉我！** 🚀

