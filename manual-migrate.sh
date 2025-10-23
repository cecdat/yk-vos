#!/bin/bash
# 手动执行数据库迁移脚本

set -e

echo "========================================"
echo "🔧 手动执行数据库迁移"
echo "========================================"
echo ""

# 检查后端容器是否运行
if ! docker-compose ps backend | grep -q "Up"; then
    echo "❌ 后端容器未运行，正在启动..."
    docker-compose up -d backend
    echo "⏳ 等待后端容器启动..."
    sleep 5
fi

echo "📦 进入后端容器执行迁移..."
echo ""

# 执行迁移
docker-compose exec backend bash -c "
cd /srv/app
echo '当前目录: \$(pwd)'
echo '检查 alembic.ini...'
ls -la alembic.ini
echo ''
echo '查看当前迁移状态...'
alembic current
echo ''
echo '执行迁移...'
alembic upgrade head
echo ''
echo '✅ 迁移完成！'
"

echo ""
echo "📊 检查数据库表..."
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt"

echo ""
echo "========================================"
echo "✨ 完成！"
echo "========================================"

