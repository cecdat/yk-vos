#!/bin/bash
# Docker 容器启动脚本

set -e

echo "🚀 正在启动 YK-VOS Backend..."

# 等待数据库就绪
echo "⏳ 等待 PostgreSQL 数据库就绪..."
while ! pg_isready -h postgres -U ${POSTGRES_USER:-vos_user} > /dev/null 2>&1; do
  echo "   数据库未就绪，等待中..."
  sleep 2
done
echo "✅ 数据库已就绪"

# 运行数据库迁移
echo "📦 运行数据库迁移..."
cd /srv/app
alembic upgrade head
echo "✅ 数据库迁移完成"

# 检查是否需要创建管理员账户
echo "👤 检查管理员账户..."
python -c "
from app.core.db import SessionLocal
from app.models.user import User

db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
if not admin:
    print('   创建默认管理员账户...')
    from app.scripts.init_admin import create_admin_user
    create_admin_user()
    print('   ✅ 管理员账户已创建 (admin/admin123)')
else:
    print('   ✅ 管理员账户已存在')
db.close()
"

# 启动应用
echo "🎉 启动 FastAPI 应用..."
cd /srv
exec "$@"

