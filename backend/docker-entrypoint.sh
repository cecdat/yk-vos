#!/bin/bash
# Docker 容器启动脚本

set -e

# 设置 UTF-8 编码
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

echo "🚀 正在启动 YK-VOS Backend..."

# 等待数据库就绪
echo "⏳ 等待 PostgreSQL 数据库就绪..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
  if pg_isready -h postgres -U ${POSTGRES_USER:-vos_user} > /dev/null 2>&1; then
    echo "✅ 数据库已就绪"
    break
  fi
  attempt=$((attempt + 1))
  echo "   等待数据库... ($attempt/$max_attempts)"
  sleep 2
done

if [ $attempt -eq $max_attempts ]; then
  echo "❌ 错误: PostgreSQL 在 $max_attempts 次尝试后仍未就绪"
  exit 1
fi

# 运行数据库迁移
echo "📦 运行数据库迁移..."
cd /srv/app
if alembic upgrade head; then
  echo "✅ 数据库迁移完成"
else
  echo "❌ 数据库迁移失败"
  exit 1
fi

# 检查是否需要创建管理员账户
echo "👤 检查管理员账户..."
cd /srv
export PYTHONPATH=/srv:$PYTHONPATH

# 确保 DATABASE_URL 环境变量存在
if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="postgresql://vos_user:vos_password@postgres:5432/vosadmin"
    echo "⚠️  未设置 DATABASE_URL，使用默认值: $DATABASE_URL"
fi

echo "🔍 使用数据库连接: $DATABASE_URL"

python3 -c "
import sys
import os
sys.path.insert(0, '/srv')

# 确保环境变量被传递
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'postgresql://vos_user:vos_password@postgres:5432/vosadmin'

try:
    from app.scripts.init_admin import run as create_admin
    create_admin()
    print('✅ 管理员账户已初始化')
except Exception as e:
    print(f'⚠️  警告: 无法初始化管理员账户: {e}')
    import traceback
    traceback.print_exc()
    # 不因为这个失败而退出
" || true

# 启动应用
echo "🎉 启动 FastAPI 应用..."
cd /srv
exec "$@"

