#!/bin/bash

# 远程服务器迁移修复脚本

echo "🔍 检查后端容器日志..."
docker-compose logs backend --tail=100 | grep -A 5 -B 5 "迁移"

echo ""
echo "🔍 检查后端容器是否运行..."
docker-compose ps backend

echo ""
echo "🔍 手动执行数据库迁移..."
docker-compose exec backend alembic upgrade head

echo ""
echo "🔍 验证迁移状态..."
docker-compose exec backend alembic current

echo ""
echo "🔍 检查vos_health_checks表是否存在..."
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\d vos_health_checks"

echo ""
echo "✅ 检查完成！"

