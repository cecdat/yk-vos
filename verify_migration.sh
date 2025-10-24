#!/bin/bash

echo "🔍 方法1：在正确的目录执行 alembic 命令"
docker-compose exec backend sh -c "cd /srv/app && alembic current"

echo ""
echo "🔍 方法2：直接检查数据库中的表"
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt" | grep vos_health_checks

echo ""
echo "🔍 方法3：检查表结构"
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\d vos_health_checks"

echo ""
echo "🔍 方法4：查看alembic版本表"
docker-compose exec postgres psql -U vos_user -d vosadmin -c "SELECT * FROM alembic_version;"

echo ""
echo "🔍 方法5：检查后端服务是否正常运行"
docker-compose ps backend

echo ""
echo "🔍 方法6：测试后端API"
curl -s http://localhost:8000/health || echo "后端服务未响应"

