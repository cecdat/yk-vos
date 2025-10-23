#!/bin/bash

# YK-VOS 快速更新脚本
# 适用于：日常代码更新和重启服务
# 使用方法：bash quick-update.sh

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   YK-VOS 快速更新部署                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# 1. 拉取最新代码
echo -e "${BLUE}[1/3]${NC} 拉取最新代码..."
if [ -d ".git" ]; then
    git pull
    echo -e "${GREEN}✓${NC} 代码已更新"
else
    echo -e "${YELLOW}⚠${NC} 非 Git 仓库，跳过拉取"
fi

# 2. 重启服务
echo ""
echo -e "${BLUE}[2/3]${NC} 重启服务..."
docker-compose restart backend frontend celery-worker celery-beat
echo -e "${GREEN}✓${NC} 服务已重启"

# 3. 检查健康状态
echo ""
echo -e "${BLUE}[3/3]${NC} 检查服务状态..."
sleep 3

# 检查后端
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 后端服务正常"
else
    echo -e "${YELLOW}⚠${NC} 后端服务检查失败，请查看日志"
fi

# 检查前端
if curl -s -I http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 前端服务正常"
else
    echo -e "${YELLOW}⚠${NC} 前端服务检查失败，请查看日志"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ 快速更新完成！${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "📝 常用命令："
echo "  查看日志: docker-compose logs -f"
echo "  查看状态: docker-compose ps"
echo "  完整升级: bash upgrade.sh"
echo ""

