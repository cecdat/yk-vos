#!/bin/bash
# Docker 容器启动脚本 - ClickHouse 架构版本

set -e

# 设置 UTF-8 编码
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

echo "🚀 正在启动 YK-VOS Backend (ClickHouse 架构)..."
echo ""

# 输出配置信息
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 数据库配置信息"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PostgreSQL (配置数据):"
echo "  地址: postgres:5432"
echo "  数据库: ${POSTGRES_DB:-vosadmin}"
echo "  用户: ${POSTGRES_USER:-vos_user}"
echo ""
echo "ClickHouse (话单数据):"
echo "  地址: ${CLICKHOUSE_HOST:-clickhouse}:${CLICKHOUSE_PORT:-9000}"
echo "  数据库: ${CLICKHOUSE_DATABASE:-vos_cdrs}"
echo "  用户: ${CLICKHOUSE_USER:-vos_user}"
echo "  密码: ${CLICKHOUSE_PASSWORD:-(未设置)}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 等待 PostgreSQL 数据库就绪
echo "⏳ 等待 PostgreSQL 数据库就绪..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
  if pg_isready -h postgres -U ${POSTGRES_USER:-vos_user} -d ${POSTGRES_DB:-vosadmin} > /dev/null 2>&1; then
    echo "✅ PostgreSQL 已就绪"
    break
  fi
  attempt=$((attempt + 1))
  echo "   等待 PostgreSQL... ($attempt/$max_attempts)"
  sleep 2
done

if [ $attempt -eq $max_attempts ]; then
  echo "❌ 错误: PostgreSQL 在 $max_attempts 次尝试后仍未就绪"
  exit 1
fi

# 等待 ClickHouse 数据库就绪
echo "⏳ 等待 ClickHouse 数据库就绪..."
attempt=0

while [ $attempt -lt $max_attempts ]; do
  # 尝试连接 ClickHouse
  if timeout 5 bash -c "echo 'SELECT 1' | nc -w 2 ${CLICKHOUSE_HOST:-clickhouse} ${CLICKHOUSE_PORT:-9000}" > /dev/null 2>&1; then
    echo "✅ ClickHouse 已就绪"
    break
  fi
  attempt=$((attempt + 1))
  echo "   等待 ClickHouse... ($attempt/$max_attempts)"
  sleep 2
done

if [ $attempt -eq $max_attempts ]; then
  echo "⚠️  警告: ClickHouse 在 $max_attempts 次尝试后仍未就绪"
  echo "   将继续启动，但话单查询功能可能不可用"
fi

# 清理 Python 缓存（避免使用旧的 .pyc 文件）
echo ""
echo "🧹 清理 Python 缓存..."
find /srv -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find /srv -type f -name "*.pyc" -delete 2>/dev/null || true
find /srv -type f -name "*.pyo" -delete 2>/dev/null || true
echo "✅ Python 缓存已清理"

# 运行数据库迁移（PostgreSQL）
echo ""
echo "📦 运行数据库迁移 (PostgreSQL)..."
cd /srv/app
if alembic upgrade head; then
  echo "✅ 数据库迁移完成"
else
  echo "❌ 数据库迁移失败"
  exit 1
fi

# 检查是否需要创建管理员账户
echo ""
echo "👤 检查管理员账户..."
cd /srv
export PYTHONPATH=/srv:$PYTHONPATH

# 确保 DATABASE_URL 环境变量存在
if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="postgresql://vos_user:vos_password@postgres:5432/vosadmin"
    echo "⚠️  未设置 DATABASE_URL，使用默认值"
fi

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

# 测试 ClickHouse 连接
echo ""
echo "🔍 测试 ClickHouse 连接..."
python3 -c "
import sys
import os
sys.path.insert(0, '/srv')

try:
    from app.core.clickhouse_db import get_clickhouse_db
    ch_db = get_clickhouse_db()
    if ch_db.ping():
        print('✅ ClickHouse 连接测试成功')
        # 获取表信息
        result = ch_db.execute('SHOW TABLES FROM vos_cdrs')
        tables = [row[0] for row in result]
        if 'cdrs' in tables:
            print(f'✅ ClickHouse 表已就绪: {len(tables)} 个表')
        else:
            print('⚠️  ClickHouse cdrs 表尚未创建')
    else:
        print('⚠️  ClickHouse 连接测试失败')
except Exception as e:
    print(f'⚠️  ClickHouse 连接失败: {e}')
    print('   话单查询功能将不可用')
" || true

# 启动应用
echo ""
echo "🎉 启动 FastAPI 应用..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cd /srv
exec "$@"

