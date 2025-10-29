#!/bin/bash
# 数据恢复脚本
# 用于从备份文件恢复YK-VOS数据

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

# 配置
PROJECT_DIR="/opt/yk-vos"
RESTORE_DIR="/tmp/yk-vos-restore"

# 显示使用说明
show_usage() {
    echo "用法: $0 <备份文件>"
    echo
    echo "示例:"
    echo "  $0 /opt/yk-vos-backups/backup-20240101-120000.tar.gz"
    echo
    echo "可用的备份文件:"
    ls -la /opt/yk-vos-backups/*.tar.gz 2>/dev/null || echo "  无可用备份文件"
}

# 检查备份文件
check_backup_file() {
    local backup_file="$1"
    
    if [[ -z "$backup_file" ]]; then
        log_error "请指定备份文件"
        show_usage
        exit 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi
    
    if [[ ! "$backup_file" =~ \.tar\.gz$ ]]; then
        log_error "备份文件格式不正确，应为.tar.gz文件"
        exit 1
    fi
    
    log_success "备份文件检查通过: $backup_file"
}

# 解压备份文件
extract_backup() {
    local backup_file="$1"
    
    log_info "解压备份文件..."
    
    # 创建临时目录
    rm -rf "$RESTORE_DIR"
    mkdir -p "$RESTORE_DIR"
    
    # 解压备份文件
    tar -xzf "$backup_file" -C "$RESTORE_DIR"
    
    if [[ $? -eq 0 ]]; then
        log_success "备份文件解压完成"
    else
        log_error "备份文件解压失败"
        exit 1
    fi
    
    # 查找解压后的目录
    RESTORE_DATA_DIR=$(find "$RESTORE_DIR" -type d -name "backup-*" | head -n 1)
    
    if [[ -z "$RESTORE_DATA_DIR" ]]; then
        log_error "未找到备份数据目录"
        exit 1
    fi
    
    log_success "备份数据目录: $RESTORE_DATA_DIR"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    
    cd "$PROJECT_DIR"
    docker compose down
    
    # 等待服务完全停止
    sleep 10
    
    log_success "服务已停止"
}

# 恢复PostgreSQL数据库
restore_postgres() {
    log_info "恢复PostgreSQL数据库..."
    
    local backup_file="$RESTORE_DATA_DIR/postgres_backup.sql"
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "PostgreSQL备份文件不存在: $backup_file"
        return 1
    fi
    
    # 启动PostgreSQL服务
    cd "$PROJECT_DIR"
    docker compose up -d postgres
    
    # 等待PostgreSQL启动
    log_info "等待PostgreSQL启动..."
    sleep 30
    
    # 检查PostgreSQL连接
    if ! docker compose exec postgres pg_isready -U yk_vos_user -d yk_vos > /dev/null 2>&1; then
        log_error "PostgreSQL数据库连接失败"
        return 1
    fi
    
    # 恢复数据库
    docker compose exec -T postgres psql -U yk_vos_user -d yk_vos < "$backup_file"
    
    if [[ $? -eq 0 ]]; then
        log_success "PostgreSQL数据库恢复完成"
    else
        log_error "PostgreSQL数据库恢复失败"
        return 1
    fi
}

# 恢复Redis数据
restore_redis() {
    log_info "恢复Redis数据..."
    
    local backup_file="$RESTORE_DATA_DIR/redis_backup.rdb"
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "Redis备份文件不存在: $backup_file"
        return 1
    fi
    
    # 启动Redis服务
    cd "$PROJECT_DIR"
    docker compose up -d redis
    
    # 等待Redis启动
    log_info "等待Redis启动..."
    sleep 10
    
    # 检查Redis连接
    if ! docker compose exec redis redis-cli ping > /dev/null 2>&1; then
        log_error "Redis数据库连接失败"
        return 1
    fi
    
    # 停止Redis服务
    docker compose stop redis
    
    # 复制备份文件到Redis数据目录
    docker compose run --rm -v "$(pwd)/redis_data:/data" redis cp "$backup_file" /data/dump.rdb
    
    # 启动Redis服务
    docker compose up -d redis
    
    log_success "Redis数据恢复完成"
}

# 恢复ClickHouse数据
restore_clickhouse() {
    log_info "恢复ClickHouse数据..."
    
    # 启动ClickHouse服务
    cd "$PROJECT_DIR"
    docker compose up -d clickhouse
    
    # 等待ClickHouse启动
    log_info "等待ClickHouse启动..."
    sleep 20
    
    # 检查ClickHouse连接
    if ! docker compose exec clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
        log_error "ClickHouse数据库连接失败"
        return 1
    fi
    
    # 恢复ClickHouse数据
    # 注意：这里需要根据实际的备份方式调整
    log_warning "ClickHouse数据恢复需要手动操作"
    log_info "请参考ClickHouse文档进行数据恢复"
    
    log_success "ClickHouse服务启动完成"
}

# 恢复配置文件
restore_config() {
    log_info "恢复配置文件..."
    
    # 恢复环境变量
    if [[ -f "$RESTORE_DATA_DIR/.env" ]]; then
        cp "$RESTORE_DATA_DIR/.env" "$PROJECT_DIR/"
        log_success "环境变量恢复完成"
    fi
    
    # 恢复Docker Compose配置
    if [[ -f "$RESTORE_DATA_DIR/docker-compose.yaml" ]]; then
        cp "$RESTORE_DATA_DIR/docker-compose.yaml" "$PROJECT_DIR/"
        log_success "Docker Compose配置恢复完成"
    fi
    
    # 恢复用户代理文件
    if [[ -f "$RESTORE_DATA_DIR/user_agents.json" ]]; then
        cp "$RESTORE_DATA_DIR/user_agents.json" "$PROJECT_DIR/"
        log_success "用户代理文件恢复完成"
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    cd "$PROJECT_DIR"
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
        return 1
    fi
}

# 验证恢复结果
verify_restore() {
    log_info "验证恢复结果..."
    
    cd "$PROJECT_DIR"
    
    # 检查服务状态
    if docker compose ps | grep -q "Up"; then
        log_success "所有服务运行正常"
    else
        log_error "部分服务运行异常"
        return 1
    fi
    
    # 检查前端访问
    if curl -s http://localhost:3000 > /dev/null; then
        log_success "前端服务正常"
    else
        log_warning "前端服务异常"
    fi
    
    # 检查后端API
    if curl -s http://localhost:3001/health > /dev/null; then
        log_success "后端服务正常"
    else
        log_warning "后端服务异常"
    fi
    
    # 检查数据库
    if docker compose exec postgres pg_isready -U yk_vos_user -d yk_vos > /dev/null 2>&1; then
        log_success "PostgreSQL数据库正常"
    else
        log_warning "PostgreSQL数据库异常"
    fi
    
    if docker compose exec redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis数据库正常"
    else
        log_warning "Redis数据库异常"
    fi
    
    log_success "恢复验证完成"
}

# 清理临时文件
cleanup_temp() {
    log_info "清理临时文件..."
    
    rm -rf "$RESTORE_DIR"
    
    log_success "临时文件清理完成"
}

# 显示恢复结果
show_restore_result() {
    log_success "数据恢复完成！"
    echo
    echo "=========================================="
    echo "  恢复信息"
    echo "=========================================="
    echo "恢复时间: $(date)"
    echo "项目目录: $PROJECT_DIR"
    echo "前端地址: http://$(hostname -I | awk '{print $1}'):3000"
    echo "后端地址: http://$(hostname -I | awk '{print $1}'):3001"
    echo
    echo "服务状态:"
    cd "$PROJECT_DIR"
    docker compose ps
    echo
    echo "注意事项:"
    echo "  • 请检查所有服务是否正常运行"
    echo "  • 请验证数据完整性"
    echo "  • 如有问题，请查看日志: docker compose logs"
    echo "=========================================="
}

# 主函数
main() {
    local backup_file="$1"
    
    log_info "开始数据恢复..."
    
    # 检查root权限
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0 <备份文件>"
        exit 1
    fi
    
    check_backup_file "$backup_file"
    extract_backup "$backup_file"
    stop_services
    restore_postgres
    restore_redis
    restore_clickhouse
    restore_config
    start_services
    verify_restore
    cleanup_temp
    show_restore_result
    
    log_success "数据恢复完成！"
}

# 执行主函数
main "$@"
