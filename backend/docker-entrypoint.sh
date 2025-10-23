#!/bin/bash
# Docker 容器启动脚本

set -e

echo "Starting YK-VOS Backend..."

# 等待数据库就绪
echo "Waiting for PostgreSQL..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
  if pg_isready -h postgres -U ${POSTGRES_USER:-vos_user} > /dev/null 2>&1; then
    echo "PostgreSQL is ready"
    break
  fi
  attempt=$((attempt + 1))
  echo "Waiting for database... ($attempt/$max_attempts)"
  sleep 2
done

if [ $attempt -eq $max_attempts ]; then
  echo "ERROR: PostgreSQL not ready after $max_attempts attempts"
  exit 1
fi

# 运行数据库迁移
echo "Running database migrations..."
cd /srv/app
if alembic upgrade head; then
  echo "Database migration completed"
else
  echo "Database migration failed"
  exit 1
fi

# 检查是否需要创建管理员账户
echo "Checking admin account..."
cd /srv
export PYTHONPATH=/srv:$PYTHONPATH
python3 -c "
import sys
sys.path.insert(0, '/srv')
try:
    from app.core.db import SessionLocal
    from app.models.user import User
    
    db = SessionLocal()
    admin = db.query(User).filter(User.username == 'admin').first()
    if not admin:
        print('Creating admin account...')
        from app.scripts.init_admin import create_admin_user
        create_admin_user()
        print('Admin account created (admin/admin123)')
    else:
        print('Admin account exists')
    db.close()
except Exception as e:
    print(f'Warning: Could not check admin account: {e}')
    # 不因为这个失败而退出
" || true

# 启动应用
echo "Starting FastAPI application..."
cd /srv
exec "$@"

