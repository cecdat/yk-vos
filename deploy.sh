#!/bin/bash

# ===================================================================
# YK-VOS 一键部署脚本 (ClickHouse 架构)
# ===================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        YK-VOS ClickHouse 架构部署脚本                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查是否为 root 用户
if [ "$EUID" -eq 0 ]; then 
   echo -e "${YELLOW}⚠️  检测到 root 用户${NC}"
fi

# 1. 创建必要的目录结构
echo -e "${BLUE}━━━ 步骤 1/8: 创建目录结构 ━━━${NC}"

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
echo -e "${BLUE}━━━ 步骤 2/8: 设置目录权限 ━━━${NC}"

# ClickHouse 使用 UID 101
if [ "$(uname)" = "Linux" ]; then
    if [ "$EUID" -eq 0 ]; then
        chown -R 101:101 data/clickhouse 2>/dev/null || true
        chmod -R 755 data/clickhouse
        echo -e "${GREEN}✓${NC} ClickHouse 数据目录权限设置完成 (UID: 101)"
    else
        sudo chown -R 101:101 data/clickhouse 2>/dev/null || {
            echo -e "${YELLOW}⚠️${NC}  无法设置 ClickHouse 目录权限，尝试继续..."
        }
        sudo chmod -R 755 data/clickhouse 2>/dev/null || true
    fi
else
    echo -e "${YELLOW}⚠️${NC}  非 Linux 系统，跳过 ClickHouse 权限设置"
fi

# PostgreSQL 使用 UID 999
if [ "$(uname)" = "Linux" ]; then
    if [ "$EUID" -eq 0 ]; then
        chown -R 999:999 data/postgres 2>/dev/null || true
        chmod -R 755 data/postgres
        echo -e "${GREEN}✓${NC} PostgreSQL 数据目录权限设置完成 (UID: 999)"
    else
        sudo chown -R 999:999 data/postgres 2>/dev/null || {
            echo -e "${YELLOW}⚠️${NC}  无法设置 PostgreSQL 目录权限，尝试继续..."
        }
        sudo chmod -R 755 data/postgres 2>/dev/null || true
    fi
fi
echo ""

# 3. 检查配置文件
echo -e "${BLUE}━━━ 步骤 3/8: 检查配置文件 ━━━${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️${NC}  未找到 .env 文件，创建默认配置..."
    
    # 生成随机密码
    PG_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
    CH_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
    SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/")
    
    cat > .env << EOF
# PostgreSQL (配置数据)
POSTGRES_USER=vos_user
POSTGRES_PASSWORD=${PG_PASSWORD}
POSTGRES_DB=vosadmin

# ClickHouse (话单数据)
CLICKHOUSE_USER=vos_user
CLICKHOUSE_PASSWORD=${CH_PASSWORD}

# Redis
REDIS_URL=redis://redis:6379

# 认证
SECRET_KEY=${SECRET_KEY}

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF
    echo -e "${GREEN}✓${NC} 已创建 .env 文件，并生成随机密码"
else
    echo -e "${GREEN}✓${NC} .env 文件已存在"
fi

# 检查 ClickHouse 初始化脚本
if [ ! -f "clickhouse/init/01_create_tables.sql" ]; then
    echo -e "${RED}✗${NC} 未找到 ClickHouse 初始化脚本: clickhouse/init/01_create_tables.sql"
    echo -e "${YELLOW}   请确保该文件存在后重新运行此脚本${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} ClickHouse 初始化脚本已就绪"
echo ""

# 4. 检查 Docker 环境
echo -e "${BLUE}━━━ 步骤 4/8: 检查 Docker 环境 ━━━${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗${NC} Docker 未安装，请先安装 Docker"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker 已安装: $(docker --version)"

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗${NC} Docker Compose 未安装"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker Compose 已安装"
echo ""

# 5. 构建基础镜像
echo -e "${BLUE}━━━ 步骤 5/8: 构建基础镜像 ━━━${NC}"

echo "🔨 构建后端基础镜像..."
if docker build -f backend/Dockerfile.base -t yk-vos-backend-base:latest backend/; then
    echo -e "${GREEN}✓${NC} 后端镜像构建成功"
else
    echo -e "${RED}✗${NC} 后端镜像构建失败"
    exit 1
fi

echo "🔨 构建前端基础镜像..."
if docker build -f frontend/Dockerfile.base -t yk-vos-frontend-base:latest frontend/; then
    echo -e "${GREEN}✓${NC} 前端镜像构建成功"
else
    echo -e "${RED}✗${NC} 前端镜像构建失败"
    exit 1
fi
echo ""

# 6. 启动服务
echo -e "${BLUE}━━━ 步骤 6/8: 启动服务 ━━━${NC}"

echo "🚀 停止现有容器..."
docker-compose down || true

echo "🚀 启动所有服务..."
docker-compose up -d

echo -e "${GREEN}✓${NC} 服务启动完成"
echo ""

# 7. 等待服务就绪
echo -e "${BLUE}━━━ 步骤 7/8: 等待服务就绪 ━━━${NC}"

echo "⏳ 等待 PostgreSQL..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U vos_user -d vosadmin > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} PostgreSQL 已就绪"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗${NC} PostgreSQL 启动超时"
        exit 1
    fi
    echo "   等待中... ($i/30)"
    sleep 2
done

echo "⏳ 等待 ClickHouse..."
for i in {1..30}; do
    if docker-compose exec -T clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} ClickHouse 已就绪"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗${NC} ClickHouse 启动超时"
        exit 1
    fi
    echo "   等待中... ($i/30)"
    sleep 2
done

echo "⏳ 等待 Redis..."
for i in {1..20}; do
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Redis 已就绪"
        break
    fi
    if [ $i -eq 20 ]; then
        echo -e "${RED}✗${NC} Redis 启动超时"
        exit 1
    fi
    echo "   等待中... ($i/20)"
    sleep 2
done

echo "⏳ 等待 Backend..."
for i in {1..40}; do
    if docker-compose exec -T backend curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend 已就绪"
        break
    fi
    if [ $i -eq 40 ]; then
        echo -e "${YELLOW}⚠️${NC}  Backend 健康检查超时，但可能已启动"
    fi
    echo "   等待中... ($i/40)"
    sleep 3
done
echo ""

# 8. 显示部署信息
echo -e "${BLUE}━━━ 步骤 8/8: 部署完成 ━━━${NC}"
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║             🎉 部署完成！                            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📋 服务访问地址：${NC}"
echo "   前端:        http://localhost:3000"
echo "   后端API:     http://localhost:8000"
echo "   API文档:     http://localhost:8000/docs"
echo "   PostgreSQL:  localhost:5430"
echo "   ClickHouse:  localhost:9000 (native), localhost:8123 (http)"
echo "   Redis:       localhost:6379"
echo ""

echo -e "${BLUE}🔐 数据库账号密码：${NC}"
if [ -f ".env" ]; then
    echo "   PostgreSQL:"
    PG_USER=$(grep "^POSTGRES_USER=" .env | cut -d'=' -f2)
    PG_PASSWORD=$(grep "^POSTGRES_PASSWORD=" .env | cut -d'=' -f2)
    echo "      用户名: ${PG_USER:-vos_user}"
    echo "      密码:   ${PG_PASSWORD:-vos_password}"
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

echo -e "${BLUE}📝 默认管理员账号：${NC}"
echo "   用户名: admin"
echo "   密码:   admin123"
echo "   ${YELLOW}⚠️  首次登录后请立即修改密码！${NC}"
echo ""

echo -e "${BLUE}🔧 常用命令：${NC}"
echo "   查看服务状态:  docker-compose ps"
echo "   查看日志:      docker-compose logs -f [service_name]"
echo "   重启服务:      docker-compose restart"
echo "   停止服务:      docker-compose down"
echo ""

echo -e "${BLUE}📚 数据存储位置：${NC}"
echo "   PostgreSQL: ./data/postgres/"
echo "   ClickHouse: ./data/clickhouse/"
echo "   ${YELLOW}提示: 请定期备份这些目录${NC}"
echo ""

echo -e "${GREEN}✅ 所有步骤完成！系统已就绪！${NC}"
echo ""
