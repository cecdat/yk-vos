#!/bin/bash

# ===================================================================
# YK-VOS ClickHouse 架构一键部署脚本
# ===================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     YK-VOS ClickHouse 架构部署脚本                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查是否为 root 用户
if [ "$EUID" -eq 0 ]; then 
   echo -e "${YELLOW}⚠️  建议不要使用 root 用户运行此脚本${NC}"
   echo -e "${YELLOW}   请使用普通用户并配置 sudo 权限${NC}"
   read -p "是否继续？(y/n) " -n 1 -r
   echo
   if [[ ! $REPLY =~ ^[Yy]$ ]]; then
       exit 1
   fi
fi

# 1. 创建必要的目录结构
echo -e "${BLUE}━━━ 步骤 1/7: 创建目录结构 ━━━${NC}"

mkdir -p data/clickhouse
mkdir -p data/postgres
mkdir -p clickhouse/init
mkdir -p backend/app/core
mkdir -p backend/app/models

echo -e "${GREEN}✓${NC} 目录结构创建完成"
echo "  - data/clickhouse   (ClickHouse 数据目录)"
echo "  - data/postgres     (PostgreSQL 数据目录)"
echo "  - clickhouse/init   (ClickHouse 初始化脚本)"
echo ""

# 2. 设置目录权限
echo -e "${BLUE}━━━ 步骤 2/7: 设置目录权限 ━━━${NC}"

# ClickHouse 使用 UID 101
if [ "$(uname)" = "Linux" ]; then
    sudo chown -R 101:101 data/clickhouse || true
    sudo chmod -R 755 data/clickhouse
    echo -e "${GREEN}✓${NC} ClickHouse 数据目录权限设置完成 (UID: 101)"
else
    echo -e "${YELLOW}⚠️${NC}  非 Linux 系统，跳过权限设置"
fi

# PostgreSQL 使用 UID 999
if [ "$(uname)" = "Linux" ]; then
    sudo chown -R 999:999 data/postgres || true
    sudo chmod -R 755 data/postgres
    echo -e "${GREEN}✓${NC} PostgreSQL 数据目录权限设置完成 (UID: 999)"
fi
echo ""

# 3. 检查配置文件
echo -e "${BLUE}━━━ 步骤 3/7: 检查配置文件 ━━━${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️${NC}  未找到 .env 文件，创建默认配置..."
    cat > .env << 'EOF'
# PostgreSQL (配置数据)
POSTGRES_USER=vos_user
POSTGRES_PASSWORD=vos_password_change_me
POSTGRES_DB=vosadmin

# ClickHouse (话单数据)
CLICKHOUSE_USER=vos_user
CLICKHOUSE_PASSWORD=clickhouse_password_change_me

# Redis
REDIS_URL=redis://redis:6379

# 认证
SECRET_KEY=your-secret-key-please-change-in-production

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF
    echo -e "${GREEN}✓${NC} 已创建默认 .env 文件"
    echo -e "${RED}⚠️  请修改默认密码后再启动服务！${NC}"
else
    echo -e "${GREEN}✓${NC} .env 文件已存在"
fi

# 检查 ClickHouse 初始化脚本
if [ ! -f "clickhouse/init/01_create_tables.sql" ]; then
    echo -e "${RED}✗${NC} 未找到 ClickHouse 初始化脚本"
    echo -e "${YELLOW}   请确保 clickhouse/init/01_create_tables.sql 存在${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} ClickHouse 初始化脚本已就绪"

# 检查 docker-compose 配置
if [ ! -f "docker-compose.clickhouse.yaml" ]; then
    echo -e "${RED}✗${NC} 未找到 docker-compose.clickhouse.yaml"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker Compose 配置文件已就绪"
echo ""

# 4. 检查 Docker 环境
echo -e "${BLUE}━━━ 步骤 4/7: 检查 Docker 环境 ━━━${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗${NC} Docker 未安装"
    echo "   请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker 已安装: $(docker --version)"

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗${NC} Docker Compose 未安装"
    echo "   请先安装 Docker Compose"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker Compose 已安装: $(docker-compose --version)"
echo ""

# 5. 停止现有服务（如果有）
echo -e "${BLUE}━━━ 步骤 5/7: 停止现有服务 ━━━${NC}"

if docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️${NC}  检测到运行中的服务，正在停止..."
    docker-compose down
    echo -e "${GREEN}✓${NC} 现有服务已停止"
else
    echo -e "${GREEN}✓${NC} 没有运行中的服务"
fi
echo ""

# 6. 启动服务
echo -e "${BLUE}━━━ 步骤 6/7: 启动 ClickHouse 架构服务 ━━━${NC}"

echo "正在启动服务..."
docker-compose -f docker-compose.clickhouse.yaml up -d

echo ""
echo -e "${GREEN}✓${NC} 服务启动完成！"
echo ""
echo "正在等待服务就绪..."
sleep 10

# 7. 健康检查
echo -e "${BLUE}━━━ 步骤 7/7: 健康检查 ━━━${NC}"

# 检查 ClickHouse
if docker-compose -f docker-compose.clickhouse.yaml exec -T clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} ClickHouse 运行正常"
    
    # 检查表是否创建
    TABLES=$(docker-compose -f docker-compose.clickhouse.yaml exec -T clickhouse clickhouse-client --query "SHOW TABLES FROM vos_cdrs" 2>/dev/null || echo "")
    if echo "$TABLES" | grep -q "cdrs"; then
        echo -e "${GREEN}✓${NC} 话单表已创建"
    else
        echo -e "${YELLOW}⚠️${NC}  话单表尚未创建（可能初始化脚本还在执行）"
    fi
else
    echo -e "${RED}✗${NC} ClickHouse 连接失败"
fi

# 检查 PostgreSQL
if docker-compose -f docker-compose.clickhouse.yaml exec -T postgres pg_isready -U vos_user > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} PostgreSQL 运行正常"
else
    echo -e "${RED}✗${NC} PostgreSQL 连接失败"
fi

# 检查 Redis
if docker-compose -f docker-compose.clickhouse.yaml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis 运行正常"
else
    echo -e "${RED}✗${NC} Redis 连接失败"
fi

# 检查 Backend
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend API 运行正常"
else
    echo -e "${YELLOW}⚠️${NC}  Backend API 尚未就绪（可能还在启动中）"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          🎉 部署完成！                               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 服务访问地址：${NC}"
echo "   Frontend:       http://localhost:3000"
echo "   Backend API:    http://localhost:8000"
echo "   API Docs:       http://localhost:8000/docs"
echo "   ClickHouse:     http://localhost:8123"
echo "   PostgreSQL:     localhost:5430"
echo ""
echo -e "${BLUE}🔐 数据库账号密码：${NC}"
if [ -f ".env" ]; then
    echo "   PostgreSQL:"
    POSTGRES_USER=$(grep "^POSTGRES_USER=" .env | cut -d'=' -f2)
    POSTGRES_PASSWORD=$(grep "^POSTGRES_PASSWORD=" .env | cut -d'=' -f2)
    echo "      用户名: ${POSTGRES_USER:-vos_user}"
    echo "      密码:   ${POSTGRES_PASSWORD:-vos_password}"
    echo ""
    echo "   ClickHouse:"
    CLICKHOUSE_USER=$(grep "^CLICKHOUSE_USER=" .env | cut -d'=' -f2)
    CLICKHOUSE_PASSWORD=$(grep "^CLICKHOUSE_PASSWORD=" .env | cut -d'=' -f2)
    echo "      用户名: ${CLICKHOUSE_USER:-vos_user}"
    echo "      密码:   ${CLICKHOUSE_PASSWORD:-vos_password}"
else
    echo "   PostgreSQL: vos_user / vos_password"
    echo "   ClickHouse: vos_user / vos_password"
fi
echo ""
echo -e "${BLUE}🗂️  数据存储位置：${NC}"
echo "   ClickHouse:     $(pwd)/data/clickhouse"
echo "   PostgreSQL:     $(pwd)/data/postgres"
echo ""
echo -e "${BLUE}📋 常用命令：${NC}"
echo "   查看服务状态:   docker-compose -f docker-compose.clickhouse.yaml ps"
echo "   查看日志:       docker-compose -f docker-compose.clickhouse.yaml logs -f"
echo "   停止服务:       docker-compose -f docker-compose.clickhouse.yaml down"
echo "   重启服务:       docker-compose -f docker-compose.clickhouse.yaml restart"
echo ""
echo -e "${BLUE}🔧 ClickHouse 管理：${NC}"
echo "   进入客户端:     docker-compose -f docker-compose.clickhouse.yaml exec clickhouse clickhouse-client"
echo "   查看表:         docker-compose -f docker-compose.clickhouse.yaml exec clickhouse clickhouse-client --query \"SHOW TABLES FROM vos_cdrs\""
echo "   查询数据:       docker-compose -f docker-compose.clickhouse.yaml exec clickhouse clickhouse-client --query \"SELECT COUNT(*) FROM vos_cdrs.cdrs\""
echo ""
echo -e "${YELLOW}⚠️  重要提示：${NC}"
echo "   1. 首次部署请修改 .env 文件中的默认密码"
echo "   2. 数据已映射到本地 data/ 目录，请定期备份"
echo "   3. 建议设置定期清理旧数据的策略（如保留12个月）"
echo ""
echo -e "${GREEN}✨ 祝使用愉快！${NC}"
echo ""

