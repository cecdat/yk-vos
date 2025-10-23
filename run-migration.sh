#!/bin/bash
# 运行数据库迁移脚本

echo "========================================"
echo "📦 运行数据库迁移"
echo "========================================"
echo ""

echo "📋 步骤 1: 检查后端容器状态"
echo "----------------------------------------"
if ! docker-compose ps backend | grep -q "Up"; then
    echo "❌ 后端容器未运行"
    echo ""
    read -p "是否启动后端容器? (Y/n): " START_BACKEND
    if [[ ! $START_BACKEND =~ ^[Nn]$ ]]; then
        echo "正在启动后端容器..."
        docker-compose up -d backend
        sleep 5
    else
        echo "已取消"
        exit 1
    fi
fi
echo "✅ 后端容器运行中"
echo ""

echo "📋 步骤 2: 查看当前迁移状态"
echo "----------------------------------------"
docker-compose exec backend bash -c "cd /srv/app && alembic current"
echo ""

echo "📋 步骤 3: 执行数据库迁移"
echo "----------------------------------------"
docker-compose exec backend bash -c "cd /srv/app && alembic upgrade head"
echo ""

echo "📋 步骤 4: 验证迁移结果"
echo "----------------------------------------"
echo "查看数据库表列表..."
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt"
echo ""

echo "检查 customers 表结构..."
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\d customers"
echo ""

echo "========================================"
echo "✅ 迁移完成！"
echo "========================================"
echo ""
echo "💡 提示："
echo "  如果迁移失败，查看详细日志："
echo "    docker-compose logs backend"
echo ""

