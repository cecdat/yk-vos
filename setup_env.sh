#!/bin/bash
# YK-VOS 环境变量快速配置脚本

echo "🚀 开始配置 YK-VOS 环境变量..."

# 生成随机密钥
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "yk-vos-secret-key-2025-please-change-me")

# 后端环境变量
cat > backend/.env << EOF
# Database Configuration
DATABASE_URL=postgresql://vos:vos123@db:5432/vosdb

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# JWT Secret Key
SECRET_KEY=${SECRET_KEY}

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=YK-VOS API

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF

echo "✅ 后端环境变量已创建: backend/.env"

# 前端环境变量
cat > frontend/.env << 'EOF'
# API Base URL
# 本地开发使用 http://localhost:8000/api/v1
# Docker 环境使用 http://backend:8000/api/v1
# 生产环境修改为实际服务器地址
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
EOF

echo "✅ 前端环境变量已创建: frontend/.env"

echo ""
echo "🎉 环境变量配置完成！"
echo ""
echo "📝 重要提示："
echo "   - 已生成随机 SECRET_KEY"
echo "   - 前端默认使用 http://localhost:8000/api/v1"
echo "   - 如需修改，请编辑 frontend/.env"
echo ""
echo "▶️  下一步: 运行 docker-compose up --build -d"
echo ""

