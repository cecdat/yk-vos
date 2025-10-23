#!/bin/bash
# 验证数据库配置脚本

echo "========================================"
echo "🔍 验证数据库配置"
echo "========================================"
echo ""

echo "📋 1. 检查环境变量"
echo "----------------------------------------"
echo "Backend 容器中的环境变量："
docker-compose exec backend bash -c 'echo "DATABASE_URL: $DATABASE_URL"'
echo ""

echo "📋 2. 检查 PostgreSQL 配置"
echo "----------------------------------------"
echo "PostgreSQL 容器中的环境变量："
docker-compose exec postgres bash -c 'echo "POSTGRES_USER: $POSTGRES_USER"; echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"; echo "POSTGRES_DB: $POSTGRES_DB"'
echo ""

echo "📋 3. 列出所有数据库"
echo "----------------------------------------"
docker-compose exec postgres psql -U vos_user -lqt | cut -d \| -f 1 | sed '/^\s*$/d'
echo ""

echo "📋 4. 测试连接"
echo "----------------------------------------"
echo "测试连接到 vosadmin 数据库："
if docker-compose exec postgres psql -U vos_user -d vosadmin -c "SELECT 'Connection successful!' as status;" 2>/dev/null; then
    echo "✅ 数据库连接成功！"
else
    echo "❌ 数据库连接失败"
fi
echo ""

echo "📋 5. 检查用户表"
echo "----------------------------------------"
echo "查询用户表中的记录数："
docker-compose exec postgres psql -U vos_user -d vosadmin -c "SELECT COUNT(*) as user_count FROM users;"
echo ""

echo "========================================"
echo "✨ 验证完成！"
echo "========================================"

