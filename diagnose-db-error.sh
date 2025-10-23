#!/bin/bash
# 诊断数据库连接错误脚本

echo "========================================"
echo "🔍 诊断数据库连接错误"
echo "========================================"
echo ""

echo "📋 1. 检查容器环境变量"
echo "----------------------------------------"
echo ""
echo "Backend 容器的 DATABASE_URL:"
docker-compose exec backend bash -c 'echo $DATABASE_URL' || echo "Backend 容器未运行"
echo ""
echo "Celery Worker 的 DATABASE_URL:"
docker-compose exec celery-worker bash -c 'echo $DATABASE_URL' || echo "Celery Worker 容器未运行"
echo ""
echo "Celery Beat 的 DATABASE_URL:"
docker-compose exec celery-beat bash -c 'echo $DATABASE_URL' || echo "Celery Beat 容器未运行"
echo ""

echo "📋 2. 检查 PostgreSQL 环境变量"
echo "----------------------------------------"
docker-compose exec postgres bash -c 'echo "POSTGRES_DB: $POSTGRES_DB"'
echo ""

echo "📋 3. 列出所有数据库"
echo "----------------------------------------"
docker-compose exec postgres psql -U vos_user -lqt | cut -d \| -f 1 | sed '/^\s*$/d'
echo ""

echo "📋 4. 检查后端容器中的配置文件"
echo "----------------------------------------"
echo "检查 backend/app/core/config.py 中的默认值:"
docker-compose exec backend grep -A 1 "DATABASE_URL:" /srv/app/core/config.py || echo "无法读取配置文件"
echo ""

echo "📋 5. 检查镜像构建时间"
echo "----------------------------------------"
docker images | grep yk-vos
echo ""

echo "📋 6. 最近的数据库连接错误"
echo "----------------------------------------"
docker-compose logs postgres | grep "FATAL" | tail -10
echo ""

echo "========================================"
echo "💡 诊断建议"
echo "========================================"
echo ""
echo "如果看到以下情况，需要重新构建镜像："
echo "  1. DATABASE_URL 中包含 'vos_db' 而不是 'vosadmin'"
echo "  2. 配置文件中的默认值还是 'vos_db'"
echo "  3. 镜像构建时间早于代码修改时间"
echo ""
echo "解决方案："
echo "  方案 1: 运行重新构建脚本"
echo "    chmod +x rebuild-and-deploy.sh"
echo "    ./rebuild-and-deploy.sh"
echo ""
echo "  方案 2: 手动重新构建"
echo "    docker-compose down"
echo "    docker-compose -f docker-compose.base.yaml build --no-cache"
echo "    docker-compose up -d"
echo ""

