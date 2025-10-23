#!/bin/bash
# 创建管理员账户脚本

set -e

echo "========================================"
echo "👤 创建管理员账户"
echo "========================================"
echo ""

echo "🔧 执行管理员账户初始化..."
docker-compose exec backend bash -c "
cd /srv
export PYTHONPATH=/srv:\$PYTHONPATH

# 确保数据库连接配置正确
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

try:
    create_admin()
    print(\"✅ 管理员账户创建成功！\")
except Exception as e:
    print(f\"❌ 创建失败: {e}\")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'
"

echo ""
echo "========================================"
echo "✅ 完成！"
echo "========================================"
echo ""
echo "🔑 默认管理员账户："
echo "   用户名: admin"
echo "   密码: admin123"
echo ""
echo "⚠️  请尽快登录并修改默认密码！"
echo ""
echo "🌐 访问地址："
echo "   前端: http://your-server:3000"
echo "   后端 API: http://your-server:8000"
echo ""

