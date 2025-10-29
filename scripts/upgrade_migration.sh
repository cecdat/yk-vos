#!/bin/bash
# 升级迁移脚本 - 用于已有数据的服务器
# 支持从旧版本升级到新版本，保持数据完整性

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        exit 1
    fi
}

# 检查现有安装
check_existing_installation() {
    log_info "检查现有安装..."
    
    PROJECT_DIR="/opt/yk-vos"
    
    if [[ ! -d "$PROJECT_DIR" ]]; then
        log_error "未找到现有安装目录: $PROJECT_DIR"
        log_info "请使用 fresh_install.sh 进行全新安装"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    if [[ ! -f "docker-compose.yaml" ]]; then
        log_error "未找到 docker-compose.yaml 文件"
        exit 1
    fi
    
    log_success "找到现有安装: $PROJECT_DIR"
}

# 备份现有数据
backup_data() {
    log_info "备份现有数据..."
    
    BACKUP_DIR="/opt/yk-vos-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份数据库
    log_info "备份PostgreSQL数据库..."
    docker compose exec -T postgres pg_dump -U yk_vos_user yk_vos > "$BACKUP_DIR/postgres_backup.sql"
    
    # 备份Redis数据
    log_info "备份Redis数据..."
    docker compose exec -T redis redis-cli --rdb "$BACKUP_DIR/redis_backup.rdb"
    
    # 备份ClickHouse数据
    log_info "备份ClickHouse数据..."
    docker compose exec -T clickhouse clickhouse-client --query "BACKUP DATABASE vos_cdrs TO Disk('backups', 'vos_cdrs_backup')"
    
    # 备份配置文件
    log_info "备份配置文件..."
    cp -r . "$BACKUP_DIR/config_backup/"
    
    log_success "数据备份完成: $BACKUP_DIR"
    
    # 显示备份信息
    echo "备份文件列表:"
    ls -la "$BACKUP_DIR"
}

# 停止现有服务
stop_services() {
    log_info "停止现有服务..."
    
    docker compose down
    
    # 等待服务完全停止
    sleep 10
    
    log_success "服务已停止"
}

# 更新代码
update_code() {
    log_info "更新代码..."
    
    # 检查是否有git仓库
    if [[ -d ".git" ]]; then
        log_info "从Git仓库更新代码..."
        git fetch origin
        git checkout main
        git pull origin main
    else
        log_warning "未找到Git仓库，请手动更新代码"
        log_info "请将新版本代码复制到 $PROJECT_DIR"
        read -p "按回车键继续..."
    fi
    
    log_success "代码更新完成"
}

# 更新Docker镜像
update_images() {
    log_info "更新Docker镜像..."
    
    # 拉取最新镜像
    docker compose pull
    
    # 构建新镜像
    docker compose build --no-cache
    
    log_success "Docker镜像更新完成"
}

# 执行数据库迁移
run_database_migration() {
    log_info "执行数据库迁移..."
    
    # 启动数据库服务
    docker compose up -d postgres redis clickhouse
    
    # 等待数据库启动
    log_info "等待数据库启动..."
    sleep 30
    
    # 检查数据库连接
    if ! docker compose exec postgres pg_isready -U yk_vos_user -d yk_vos; then
        log_error "PostgreSQL数据库连接失败"
        exit 1
    fi
    
    # 执行数据库迁移脚本
    log_info "执行PostgreSQL迁移脚本..."
    
    # 检查数据库版本
    DB_VERSION=$(docker compose exec -T postgres psql -U yk_vos_user -d yk_vos -t -c "SELECT version FROM db_versions ORDER BY applied_at DESC LIMIT 1;" 2>/dev/null || echo "0")
    
    log_info "当前数据库版本: $DB_VERSION"
    
    # 执行v2.3升级脚本
    if [[ "$DB_VERSION" != "2.3" ]]; then
        log_info "执行v2.3升级脚本..."
        if [[ -f "sql/upgrade_db_v2.3.sql" ]]; then
            docker compose exec -T postgres psql -U yk_vos_user -d yk_vos < sql/upgrade_db_v2.3.sql
            log_success "PostgreSQL v2.3升级完成"
        else
            log_error "未找到升级脚本: sql/upgrade_db_v2.3.sql"
            exit 1
        fi
    else
        log_warning "数据库已经是v2.3版本，跳过升级"
    fi
    
    # 执行ClickHouse升级
    log_info "执行ClickHouse升级..."
    if [[ -f "clickhouse/init/02_upgrade_add_vos_uuid.sql" ]]; then
        docker compose exec -T clickhouse clickhouse-client < clickhouse/init/02_upgrade_add_vos_uuid.sql
        log_success "ClickHouse升级完成"
    else
        log_warning "未找到ClickHouse升级脚本"
    fi
    
    log_success "数据库迁移完成"
}

# 更新环境配置
update_environment() {
    log_info "更新环境配置..."
    
    # 检查是否需要更新环境变量
    if [[ ! -f ".env" ]]; then
        log_warning "未找到.env文件，创建默认配置..."
        setup_environment
    else
        log_info "检查环境变量配置..."
        
        # 检查必要的环境变量
        if ! grep -q "JWT_SECRET_KEY" .env; then
            log_info "添加JWT_SECRET_KEY..."
            echo "JWT_SECRET_KEY=$(openssl rand -base64 64)" >> .env
        fi
        
        if ! grep -q "JWT_ALGORITHM" .env; then
            log_info "添加JWT_ALGORITHM..."
            echo "JWT_ALGORITHM=HS256" >> .env
        fi
        
        if ! grep -q "JWT_ACCESS_TOKEN_EXPIRE_MINUTES" .env; then
            log_info "添加JWT_ACCESS_TOKEN_EXPIRE_MINUTES..."
            echo "JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30" >> .env
        fi
    fi
    
    log_success "环境配置更新完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动所有服务
    docker compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 60
    
    # 检查服务状态
    if docker compose ps | grep -q "Up"; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        docker compose logs
        exit 1
    fi
}

# 验证升级结果
verify_upgrade() {
    log_info "验证升级结果..."
    
    # 检查数据库版本
    DB_VERSION=$(docker compose exec -T postgres psql -U yk_vos_user -d yk_vos -t -c "SELECT version FROM db_versions ORDER BY applied_at DESC LIMIT 1;" 2>/dev/null || echo "unknown")
    log_info "数据库版本: $DB_VERSION"
    
    # 检查VOS实例UUID
    VOS_COUNT=$(docker compose exec -T postgres psql -U yk_vos_user -d yk_vos -t -c "SELECT COUNT(*) FROM vos_instances WHERE vos_uuid IS NOT NULL;" 2>/dev/null || echo "0")
    log_info "VOS实例数量: $VOS_COUNT"
    
    # 检查服务健康状态
    if curl -s http://localhost:3001/health > /dev/null; then
        log_success "后端服务健康检查通过"
    else
        log_warning "后端服务健康检查失败"
    fi
    
    if curl -s http://localhost:3000 > /dev/null; then
        log_success "前端服务健康检查通过"
    else
        log_warning "前端服务健康检查失败"
    fi
    
    log_success "升级验证完成"
}

# 显示升级结果
show_result() {
    log_success "升级完成！"
    echo
    echo "=========================================="
    echo "  YK-VOS 升级迁移完成"
    echo "=========================================="
    echo "项目目录: $PROJECT_DIR"
    echo "前端地址: http://$(hostname -I | awk '{print $1}'):3000"
    echo "后端地址: http://$(hostname -I | awk '{print $1}'):3001"
    echo
    echo "升级内容:"
    echo "  ✓ VOS节点唯一UUID支持"
    echo "  ✓ IP变更时数据关联连续性"
    echo "  ✓ 增强的网关同步功能"
    echo "  ✓ 改进的健康检查机制"
    echo "  ✓ 数据库结构优化"
    echo
    echo "管理命令:"
    echo "  查看状态: docker compose ps"
    echo "  查看日志: docker compose logs -f"
    echo "  重启服务: docker compose restart"
    echo
    echo "日常维护:"
    echo "  日常更新: sudo ./scripts/daily_update.sh"
    echo "  数据备份: sudo ./scripts/daily_update.sh backup"
    echo "  健康检查: sudo ./scripts/daily_update.sh health-check"
    echo
    echo "备份位置: $BACKUP_DIR"
    echo "=========================================="
}

# 设置环境变量函数
setup_environment() {
    log_info "设置环境变量..."
    
    cat > .env << EOF
# 数据库配置
POSTGRES_DB=yk_vos
POSTGRES_USER=yk_vos_user
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Redis配置
REDIS_PASSWORD=$(openssl rand -base64 32)

# JWT配置
JWT_SECRET_KEY=$(openssl rand -base64 64)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=3001
FRONTEND_PORT=3000

# 时区
TZ=Asia/Shanghai
EOF
    
    log_success "环境变量设置完成"
}

# 主函数
main() {
    log_info "开始升级 YK-VOS..."
    
    check_root
    check_existing_installation
    backup_data
    stop_services
    update_code
    update_images
    run_database_migration
    update_environment
    start_services
    verify_upgrade
    show_result
    
    log_success "升级完成！"
}

# 执行主函数
main "$@"
