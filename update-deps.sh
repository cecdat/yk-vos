#!/bin/bash

# YK-VOS 依赖更新脚本
# 用于更新 Python/Node.js 依赖后重新构建基础镜像

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  YK-VOS 依赖更新工具${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查是否有变更
if git diff --quiet backend/requirements.txt frontend/package.json; then
    echo -e "${YELLOW}⚠️  没有检测到依赖变更${NC}"
    read -p "是否仍要继续重新构建？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo -e "${BLUE}[1/3]${NC} 停止运行中的服务..."
docker-compose stop backend celery-worker celery-beat frontend

echo ""
echo -e "${BLUE}[2/3]${NC} 重新构建基础镜像（可能需要几分钟）..."
docker-compose -f docker-compose.base.yaml build --no-cache

echo ""
echo -e "${BLUE}[3/3]${NC} 重启服务..."
docker-compose up -d backend celery-worker celery-beat frontend

echo ""
echo -e "${GREEN}✅ 依赖更新完成！${NC}"
echo ""
echo "查看服务状态："
docker-compose ps

echo ""
echo "查看后端日志："
echo "  docker-compose logs -f backend"
echo ""

