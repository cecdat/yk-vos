#!/bin/bash
# 数据库迁移诊断脚本

echo "========================================"
echo "🔍 YK-VOS 数据库迁移诊断"
echo "========================================"
echo ""

# 1. 检查容器状态
echo "📦 1. 检查容器状态"
echo "----------------------------------------"
docker-compose ps
echo ""

# 2. 检查后端日志
echo "📋 2. 后端容器日志（最近50行）"
echo "----------------------------------------"
docker-compose logs --tail=50 backend
echo ""

# 3. 检查数据库连接
echo "🔌 3. 检查数据库连接"
echo "----------------------------------------"
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt"
echo ""

# 4. 检查 Alembic 版本
echo "📌 4. 当前 Alembic 迁移版本"
echo "----------------------------------------"
docker-compose exec backend bash -c "cd /srv/app && alembic current"
echo ""

# 5. 检查待执行的迁移
echo "📌 5. 待执行的迁移"
echo "----------------------------------------"
docker-compose exec backend bash -c "cd /srv/app && alembic history"
echo ""

# 6. 尝试手动执行迁移
echo "🔧 6. 手动执行数据库迁移"
echo "----------------------------------------"
docker-compose exec backend bash -c "cd /srv/app && alembic upgrade head"
echo ""

# 7. 再次检查数据库表
echo "✅ 7. 检查迁移后的数据库表"
echo "----------------------------------------"
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt"
echo ""

echo "========================================"
echo "✨ 诊断完成！"
echo "========================================"

