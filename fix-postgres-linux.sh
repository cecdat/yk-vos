#!/bin/bash

# PostgreSQL 启动问题诊断和修复脚本
# 适用于 Linux 服务器

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}    PostgreSQL 启动问题诊断和修复${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 1. 停止所有服务
echo -e "${YELLOW}步骤 1/6: 停止所有服务...${NC}"
docker-compose -f docker-compose.clickhouse.yaml down -v
echo -e "${GREEN}✓${NC} 服务已停止"
echo ""

# 2. 查看 PostgreSQL 日志（如果容器还在）
echo -e "${YELLOW}步骤 2/6: 查看历史日志...${NC}"
if docker ps -a | grep -q yk_vos_postgres; then
    echo "PostgreSQL 容器日志（最后 50 行）："
    docker logs yk_vos_postgres --tail=50
else
    echo "容器已被清理，无法查看日志"
fi
echo ""

# 3. 检查数据目录
echo -e "${YELLOW}步骤 3/6: 检查数据目录...${NC}"
if [ -d "data/postgres" ]; then
    echo "PostgreSQL 数据目录存在"
    echo "目录大小: $(du -sh data/postgres 2>/dev/null | cut -f1)"
    echo "目录权限: $(ls -ld data/postgres)"
    echo "目录内容: $(ls -la data/postgres 2>/dev/null | wc -l) 个文件/目录"
    
    # 检查是否有锁文件
    if [ -f "data/postgres/postmaster.pid" ]; then
        echo -e "${RED}⚠️  发现锁文件 postmaster.pid，可能是上次异常退出${NC}"
    fi
else
    echo "PostgreSQL 数据目录不存在"
fi
echo ""

# 4. 清理旧数据
echo -e "${YELLOW}步骤 4/6: 清理旧数据...${NC}"
echo -e "${RED}警告: 即将删除 PostgreSQL 数据目录！${NC}"
echo "按 Ctrl+C 取消，或按 Enter 继续..."
read

rm -rf data/postgres
rm -rf data/clickhouse
echo -e "${GREEN}✓${NC} 旧数据已清理"
echo ""

# 5. 重新创建目录并设置权限
echo -e "${YELLOW}步骤 5/6: 创建目录并设置权限...${NC}"

# 创建目录
mkdir -p data/postgres
mkdir -p data/clickhouse

# PostgreSQL 容器使用 UID 999
chown -R 999:999 data/postgres
chmod -R 755 data/postgres

# ClickHouse 容器使用 UID 101
chown -R 101:101 data/clickhouse
chmod -R 755 data/clickhouse

echo "PostgreSQL 目录权限: $(ls -ld data/postgres)"
echo "ClickHouse 目录权限: $(ls -ld data/clickhouse)"
echo -e "${GREEN}✓${NC} 权限设置完成"
echo ""

# 6. 重新启动服务
echo -e "${YELLOW}步骤 6/6: 启动服务...${NC}"
docker-compose -f docker-compose.clickhouse.yaml up -d

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}等待服务启动...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 等待 30 秒
for i in {1..30}; do
    echo -ne "\r等待中... $i/30 秒"
    sleep 1
done
echo ""
echo ""

# 检查服务状态
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}服务状态${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
docker-compose -f docker-compose.clickhouse.yaml ps
echo ""

# 检查 PostgreSQL 健康状态
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PostgreSQL 健康检查${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if docker-compose -f docker-compose.clickhouse.yaml exec -T postgres pg_isready -U vos_user > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL 运行正常${NC}"
else
    echo -e "${RED}✗ PostgreSQL 仍然不健康${NC}"
    echo ""
    echo "查看详细日志："
    docker-compose -f docker-compose.clickhouse.yaml logs postgres --tail=100
    exit 1
fi
echo ""

# 检查 ClickHouse 健康状态
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}ClickHouse 健康检查${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if docker-compose -f docker-compose.clickhouse.yaml exec -T clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ ClickHouse 运行正常${NC}"
    
    # 检查表
    TABLES=$(docker-compose -f docker-compose.clickhouse.yaml exec -T clickhouse clickhouse-client --query "SHOW TABLES FROM vos_cdrs" 2>/dev/null || echo "")
    if echo "$TABLES" | grep -q "cdrs"; then
        echo -e "${GREEN}✓ ClickHouse 表已创建${NC}"
    else
        echo -e "${YELLOW}⚠️  ClickHouse 表尚未创建（可能初始化脚本还在执行）${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  ClickHouse 连接失败（可能还在启动中）${NC}"
fi
echo ""

# 显示所有服务的简要日志
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}各服务最新日志（最后 10 行）${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}PostgreSQL:${NC}"
docker-compose -f docker-compose.clickhouse.yaml logs postgres --tail=10
echo ""

echo -e "${YELLOW}Backend:${NC}"
docker-compose -f docker-compose.clickhouse.yaml logs backend --tail=10
echo ""

# 完成
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}修复完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "如果还有问题，请运行："
echo "  docker-compose -f docker-compose.clickhouse.yaml logs -f"
echo ""
echo "或查看特定服务的日志："
echo "  docker-compose -f docker-compose.clickhouse.yaml logs postgres"
echo "  docker-compose -f docker-compose.clickhouse.yaml logs backend"
echo ""

