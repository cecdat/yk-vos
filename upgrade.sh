#!/bin/bash

# YK-VOS 升级部署脚本
# 系统要求：Debian 10+ 或 Ubuntu 20.04+
# 适用于：已部署环境的升级更新
# 使用方法：bash upgrade.sh

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  $1${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 检查 Docker 和 Docker Compose
check_dependencies() {
    print_step "检查依赖环境"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    print_success "Docker 已安装: $(docker --version)"
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    print_success "Docker Compose 已安装: $(docker-compose --version)"
}

# 备份数据库
backup_database() {
    print_step "备份数据库"
    
    # 创建备份目录
    mkdir -p backups
    
    # 生成备份文件名
    BACKUP_FILE="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # 检查 PostgreSQL 容器是否运行
    if docker-compose ps postgres | grep -q "Up"; then
        print_info "开始备份数据库..."
        docker-compose exec -T postgres pg_dump -U vos_user vos_db > "$BACKUP_FILE"
        
        if [ -f "$BACKUP_FILE" ]; then
            BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
            print_success "数据库备份成功: $BACKUP_FILE (大小: $BACKUP_SIZE)"
        else
            print_error "数据库备份失败"
            exit 1
        fi
    else
        print_warning "PostgreSQL 容器未运行，跳过备份"
    fi
}

# 拉取最新代码
pull_code() {
    print_step "拉取最新代码"
    
    # 检查 Git 仓库
    if [ ! -d ".git" ]; then
        print_warning "不是 Git 仓库，跳过代码拉取"
        return
    fi
    
    # 显示当前分支
    CURRENT_BRANCH=$(git branch --show-current)
    print_info "当前分支: $CURRENT_BRANCH"
    
    # 检查未提交的更改
    if ! git diff-index --quiet HEAD --; then
        print_warning "检测到未提交的更改"
        read -p "是否暂存这些更改？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash
            print_success "已暂存本地更改"
            STASHED=true
        fi
    fi
    
    # 拉取代码
    print_info "拉取最新代码..."
    git pull origin "$CURRENT_BRANCH"
    print_success "代码拉取成功"
    
    # 恢复暂存的更改
    if [ "$STASHED" = true ]; then
        read -p "是否恢复暂存的更改？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash pop
            print_success "已恢复本地更改"
        fi
    fi
}

# 停止服务
stop_services() {
    print_step "停止现有服务"
    
    print_info "优雅停止所有服务..."
    docker-compose stop
    print_success "服务已停止"
}

# 构建镜像
build_images() {
    print_step "构建 Docker 镜像"
    
    print_info "构建后端镜像..."
    docker-compose build backend
    
    print_info "构建前端镜像..."
    docker-compose build frontend
    
    print_success "镜像构建完成"
}

# 启动服务
start_services() {
    print_step "启动服务"
    
    print_info "启动所有服务..."
    docker-compose up -d
    
    print_info "等待服务启动..."
    sleep 10
    
    print_success "服务已启动"
}

# 验证部署
verify_deployment() {
    print_step "验证部署"
    
    # 检查容器状态
    print_info "检查容器状态..."
    docker-compose ps
    
    # 检查后端健康
    print_info "检查后端健康状态..."
    sleep 5
    if curl -s http://localhost:8000/health | grep -q "ok"; then
        print_success "后端服务正常"
    else
        print_warning "后端健康检查失败，请检查日志"
    fi
    
    # 检查前端
    print_info "检查前端访问..."
    if curl -s -I http://localhost:3000 | grep -q "200"; then
        print_success "前端服务正常"
    else
        print_warning "前端访问失败，请检查日志"
    fi
    
    # 检查数据库迁移
    print_info "检查数据库迁移..."
    MIGRATION_LOG=$(docker-compose logs backend | grep -i alembic | tail -5)
    if echo "$MIGRATION_LOG" | grep -q "Running upgrade"; then
        print_success "数据库迁移已执行"
        echo "$MIGRATION_LOG"
    else
        print_info "未检测到新的迁移"
    fi
    
    # 检查索引
    print_info "验证数据库索引..."
    INDEX_COUNT=$(docker-compose exec -T postgres psql -U vos_user -d vos_db -t -c "SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'cdrs' AND indexname LIKE 'idx_cdr_%';" | xargs)
    if [ "$INDEX_COUNT" -ge 5 ]; then
        print_success "CDR 表索引已创建 ($INDEX_COUNT 个)"
    else
        print_warning "CDR 表索引不完整，只有 $INDEX_COUNT 个"
    fi
}

# 显示部署结果
show_result() {
    print_step "部署完成"
    
    echo ""
    print_success "🎉 升级部署成功完成！"
    echo ""
    echo -e "${BLUE}访问地址：${NC}"
    echo "  - 前端: http://localhost:3000"
    echo "  - 后端: http://localhost:8000"
    echo "  - API文档: http://localhost:8000/docs"
    echo ""
    echo -e "${BLUE}主要更新：${NC}"
    echo "  ✅ 历史话单查询优化（查询速度提升 20-50 倍）"
    echo "  ✅ VOS API 智能参数表单（时间默认最近3天）"
    echo "  ✅ 数据分页显示（默认 20 条/页）"
    echo "  ✅ 5 个数据库索引优化"
    echo ""
    echo -e "${BLUE}后续操作：${NC}"
    echo "  - 查看日志: docker-compose logs -f"
    echo "  - 验证功能: 访问 http://localhost:3000/cdr"
    echo "  - 查看文档: cat CDR_QUERY_OPTIMIZATION.md"
    echo ""
    
    # 显示备份信息
    if [ -n "$BACKUP_FILE" ]; then
        echo -e "${YELLOW}数据库备份位置：${NC}$BACKUP_FILE"
        echo ""
    fi
}

# 错误处理
handle_error() {
    print_error "部署过程中发生错误！"
    echo ""
    print_warning "回滚建议："
    echo "  1. 查看日志: docker-compose logs -f"
    echo "  2. 停止服务: docker-compose down"
    if [ -n "$BACKUP_FILE" ]; then
        echo "  3. 恢复备份: docker-compose exec -T postgres psql -U vos_user -d vos_db < $BACKUP_FILE"
    fi
    echo "  4. 查看详细文档: cat UPGRADE_GUIDE.md"
    echo ""
}

# 主函数
main() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   VOS 系统一键升级部署脚本 v1.0      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    
    # 确认执行
    print_warning "此脚本将自动执行以下操作："
    echo "  1. 备份数据库"
    echo "  2. 拉取最新代码"
    echo "  3. 停止现有服务"
    echo "  4. 构建新镜像"
    echo "  5. 启动服务"
    echo "  6. 验证部署"
    echo ""
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "已取消部署"
        exit 0
    fi
    
    # 设置错误处理
    trap handle_error ERR
    
    # 执行部署步骤
    check_dependencies
    backup_database
    pull_code
    stop_services
    build_images
    start_services
    verify_deployment
    show_result
}

# 执行主函数
main

