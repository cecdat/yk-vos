#!/bin/bash
# 修复空数据库问题

set -e

echo "========================================"
echo "🔧 修复 YK-VOS 空数据库问题"
echo "========================================"
echo ""

echo "📋 步骤 1: 检查环境变量"
echo "----------------------------------------"
docker-compose exec backend bash -c 'echo "DATABASE_URL: $DATABASE_URL"'
echo ""

echo "📋 步骤 2: 检查数据库连接"
echo "----------------------------------------"
if docker-compose exec postgres pg_isready -U vos_user; then
    echo "✅ 数据库连接正常"
else
    echo "❌ 数据库连接失败"
    exit 1
fi
echo ""

echo "📋 步骤 3: 检查数据库是否存在"
echo "----------------------------------------"
docker-compose exec postgres psql -U vos_user -lqt | cut -d \| -f 1 | grep -qw vosadmin && echo "✅ 数据库 vosadmin 存在" || echo "❌ 数据库 vosadmin 不存在"
echo ""

echo "📋 步骤 4: 查看当前数据库表"
echo "----------------------------------------"
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt"
echo ""

echo "📋 步骤 5: 检查 Alembic 配置"
echo "----------------------------------------"
docker-compose exec backend bash -c "cd /srv/app && ls -la alembic.ini && cat alembic.ini | grep script_location"
echo ""

echo "📋 步骤 6: 查看迁移文件"
echo "----------------------------------------"
docker-compose exec backend bash -c "ls -la /srv/app/alembic/versions/"
echo ""

echo "📋 步骤 7: 执行数据库迁移"
echo "----------------------------------------"
docker-compose exec backend bash -c "
export DATABASE_URL='postgresql://vos_user:vos_password@postgres:5432/vosadmin'
cd /srv/app
echo '当前目录: \$(pwd)'
echo '执行迁移...'
alembic upgrade head
"
echo ""

echo "📋 步骤 8: 验证表已创建"
echo "----------------------------------------"
docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt"
echo ""

echo "📋 步骤 9: 创建管理员账户"
echo "----------------------------------------"
docker-compose exec backend bash -c "
cd /srv
export PYTHONPATH=/srv:\$PYTHONPATH
export DATABASE_URL=\${DATABASE_URL:-postgresql://vos_user:vos_password@postgres:5432/vosadmin}
echo \"使用数据库连接: \$DATABASE_URL\"

python3 -c '
import sys
import os
sys.path.insert(0, \"/srv\")

# 确保环境变量被传递
if \"DATABASE_URL\" not in os.environ:
    os.environ[\"DATABASE_URL\"] = \"postgresql://vos_user:vos_password@postgres:5432/vosadmin\"

from app.scripts.init_admin import run as create_admin
create_admin()
print(\"✅ 管理员账户已创建\")
'
"
echo ""

echo "========================================"
echo "✅ 修复完成！"
echo "========================================"
echo ""
echo "🔑 默认管理员账户："
echo "   用户名: admin"
echo "   密码: admin123"
echo ""
echo "⚠️  请尽快修改默认密码！"

