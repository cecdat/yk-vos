#!/bin/bash
# 数据库备份恢复脚本
# 支持数据备份、恢复、管理等功能

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
PROJECT_DIR="/data/yk-vos"
BACKUP_BASE_DIR="/data/yk-vos-backups"
BACKUP_DIR="$BACKUP_BASE_DIR/backup-$(date +%Y%m%d-%H%M%S)"

# 读取环境变量
load_environment() {
    log_info "读取环境配置..."
    
    if [[ -f ".env" ]]; then
        # 加载环境变量
        export $(grep -v '^#' .env | xargs)
        log_success "环境变量加载完成"
    else
        log_warning "未找到.env文件，使用默认配置"
        # 设置默认值
        export POSTGRES_DB=${POSTGRES_DB:-"yk_vos"}
        export POSTGRES_USER=${POSTGRES_USER:-"yk_vos_user"}
        export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-"password"}
    fi
    
    log_info "数据库配置: $POSTGRES_USER@$POSTGRES_DB"
}

# 显示使用说明
show_usage() {
    echo "用法: $0 [选项] [参数]"
    echo
    echo "选项:"
    echo "  backup           数据备份"
    echo "  restore <file>   数据恢复"
    echo "  list             列出备份文件"
    echo "  cleanup          清理旧备份"
    echo "  info <file>      查看备份信息"
    echo
    echo "示例:"
    echo "  $0 backup                    # 备份数据"
    echo "  $0 restore backup-20240101.tar.gz  # 恢复数据"
    echo "  $0 list                      # 列出备份文件"
    echo "  $0 cleanup                   # 清理旧备份"
    echo "  $0 info backup-20240101.tar.gz    # 查看备份信息"
}

# 创建备份目录
create_backup_dir() {
    log_info "创建备份目录: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
}

# 备份PostgreSQL数据库
backup_postgres() {
    log_info "备份PostgreSQL数据库..."
    
    if docker compose exec postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
        docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_DIR/postgres_backup.sql"
        log_success "PostgreSQL备份完成: $BACKUP_DIR/postgres_backup.sql"
    else
        log_error "PostgreSQL数据库连接失败"
        return 1
    fi
}

# 备份Redis数据
backup_redis() {
    log_info "备份Redis数据..."
    
    if docker compose exec redis redis-cli ping > /dev/null 2>&1; then
        docker compose exec -T redis redis-cli --rdb "$BACKUP_DIR/redis_backup.rdb"
        log_success "Redis备份完成: $BACKUP_DIR/redis_backup.rdb"
    else
        log_error "Redis数据库连接失败"
        return 1
    fi
}

# 备份ClickHouse数据
backup_clickhouse() {
    log_info "备份ClickHouse数据..."
    
    if docker compose exec clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
        BACKUP_NAME="vos_cdrs_backup_$(date +%Y%m%d_%H%M%S)"
        docker compose exec -T clickhouse clickhouse-client --query "BACKUP DATABASE vos_cdrs TO Disk('backups', '$BACKUP_NAME')"
        log_success "ClickHouse备份完成: $BACKUP_NAME"
    else
        log_error "ClickHouse数据库连接失败"
        return 1
    fi
}

# 备份配置文件
backup_config() {
    log_info "备份配置文件..."
    
    # 备份环境变量
    if [[ -f ".env" ]]; then
        cp .env "$BACKUP_DIR/"
        log_success "环境变量备份完成"
    fi
    
    # 备份docker-compose文件
    if [[ -f "docker-compose.yaml" ]]; then
        cp docker-compose.yaml "$BACKUP_DIR/"
        log_success "Docker Compose配置备份完成"
    fi
    
    # 备份用户代理文件
    if [[ -f "user_agents.json" ]]; then
        cp user_agents.json "$BACKUP_DIR/"
        log_success "用户代理文件备份完成"
    fi
}

# 创建备份信息文件
create_backup_info() {
    log_info "创建备份信息文件..."
    
    cat > "$BACKUP_DIR/backup_info.txt" << EOF
YK-VOS 数据备份信息
==================

备份时间: $(date)
备份目录: $BACKUP_DIR
项目目录: $PROJECT_DIR

包含内容:
- PostgreSQL数据库备份
- Redis数据备份
- ClickHouse数据备份
- 配置文件备份

服务版本信息:
$(docker compose version)

Docker镜像信息:
$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | grep yk-vos)

系统信息:
$(uname -a)
$(cat /etc/os-release | head -n 3)
EOF
    
    log_success "备份信息文件创建完成"
}

# 压缩备份文件
compress_backup() {
    log_info "压缩备份文件..."
    
    cd "$BACKUP_BASE_DIR"
    tar -czf "backup-$(date +%Y%m%d-%H%M%S).tar.gz" "backup-$(date +%Y%m%d-%H%M%S)"
    
    if [[ $? -eq 0 ]]; then
        log_success "备份文件压缩完成"
        # 删除未压缩的目录
        rm -rf "backup-$(date +%Y%m%d-%H%M%S)"
    else
        log_error "备份文件压缩失败"
        return 1
    fi
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理旧备份文件..."
    
    # 保留最近7天的备份
    find "$BACKUP_BASE_DIR" -name "backup-*.tar.gz" -mtime +7 -delete
    
    log_success "旧备份文件清理完成"
}

# 数据恢复功能
restore_data() {
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
    
    log_info "开始数据恢复..."
    
    # 检查项目目录
    if [[ ! -d "$PROJECT_DIR" ]]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # 停止服务
    log_info "停止服务..."
    docker compose down
    sleep 10
    
    # 解压备份文件
    local restore_dir="/tmp/yk-vos-restore"
    rm -rf "$restore_dir"
    mkdir -p "$restore_dir"
    
    log_info "解压备份文件..."
    tar -xzf "$backup_file" -C "$restore_dir"
    
    local restore_data_dir=$(find "$restore_dir" -type d -name "backup-*" | head -n 1)
    
    if [[ -z "$restore_data_dir" ]]; then
        log_error "未找到备份数据目录"
        exit 1
    fi
    
    # 恢复PostgreSQL数据库
    log_info "恢复PostgreSQL数据库..."
    docker compose up -d postgres
    sleep 30
    
    if docker compose exec postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
        docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$restore_data_dir/postgres_backup.sql"
        log_success "PostgreSQL数据库恢复完成"
    else
        log_error "PostgreSQL数据库连接失败"
        exit 1
    fi
    
    # 恢复Redis数据
    log_info "恢复Redis数据..."
    docker compose up -d redis
    sleep 10
    
    if docker compose exec redis redis-cli ping > /dev/null 2>&1; then
        docker compose stop redis
        docker compose run --rm -v "$(pwd)/redis_data:/data" redis cp "$restore_data_dir/redis_backup.rdb" /data/dump.rdb
        docker compose up -d redis
        log_success "Redis数据恢复完成"
    else
        log_error "Redis数据库连接失败"
        exit 1
    fi
    
    # 恢复配置文件
    log_info "恢复配置文件..."
    cp "$restore_data_dir/.env" "$PROJECT_DIR/" 2>/dev/null || log_warning "未找到.env文件"
    cp "$restore_data_dir/docker-compose.yaml" "$PROJECT_DIR/" 2>/dev/null || log_warning "未找到docker-compose.yaml文件"
    cp "$restore_data_dir/user_agents.json" "$PROJECT_DIR/" 2>/dev/null || log_warning "未找到user_agents.json文件"
    
    # 启动服务
    log_info "启动服务..."
    docker compose up -d
    sleep 60
    
    # 验证恢复结果
    if docker compose ps | grep -q "Up"; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        docker compose logs
        exit 1
    fi
    
    # 清理临时文件
    rm -rf "$restore_dir"
    
    log_success "数据恢复完成！"
}

# 列出备份文件
list_backups() {
    log_info "备份文件列表:"
    echo
    echo "=========================================="
    echo "  备份文件列表"
    echo "=========================================="
    
    if [[ -d "$BACKUP_BASE_DIR" ]]; then
        ls -lh "$BACKUP_BASE_DIR"/*.tar.gz 2>/dev/null || echo "  无备份文件"
        echo
        echo "备份目录: $BACKUP_BASE_DIR"
        echo "总大小: $(du -sh "$BACKUP_BASE_DIR" 2>/dev/null | cut -f1)"
    else
        echo "  备份目录不存在"
    fi
    
    echo "=========================================="
}

# 清理旧备份
cleanup_backups() {
    log_info "清理旧备份文件..."
    
    if [[ -d "$BACKUP_BASE_DIR" ]]; then
        # 保留最近7天的备份
        find "$BACKUP_BASE_DIR" -name "backup-*.tar.gz" -mtime +7 -delete
        log_success "旧备份文件清理完成"
    else
        log_warning "备份目录不存在"
    fi
}

# 查看备份信息
show_backup_info() {
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
    
    log_info "备份文件信息: $backup_file"
    echo
    echo "=========================================="
    echo "  备份文件信息"
    echo "=========================================="
    echo "文件名: $(basename "$backup_file")"
    echo "大小: $(ls -lh "$backup_file" | awk '{print $5}')"
    echo "修改时间: $(ls -l "$backup_file" | awk '{print $6, $7, $8}')"
    echo
    
    # 解压并查看备份信息
    local temp_dir="/tmp/yk-vos-backup-info"
    rm -rf "$temp_dir"
    mkdir -p "$temp_dir"
    
    tar -xzf "$backup_file" -C "$temp_dir" --wildcards "*/backup_info.txt" 2>/dev/null || true
    
    local info_file=$(find "$temp_dir" -name "backup_info.txt" | head -n 1)
    if [[ -f "$info_file" ]]; then
        echo "备份信息:"
        cat "$info_file"
    else
        echo "未找到备份信息文件"
    fi
    
    rm -rf "$temp_dir"
    echo "=========================================="
}

# 显示备份结果
show_backup_result() {
    log_success "备份完成！"
    echo
    echo "=========================================="
    echo "  备份信息"
    echo "=========================================="
    echo "备份目录: $BACKUP_BASE_DIR"
    echo "备份时间: $(date)"
    echo
    echo "备份文件:"
    ls -lh "$BACKUP_BASE_DIR"/*.tar.gz 2>/dev/null || echo "  无备份文件"
    echo
    echo "备份大小:"
    du -sh "$BACKUP_BASE_DIR" 2>/dev/null || echo "  无法计算"
    echo
    echo "管理命令:"
    echo "  恢复数据: $0 restore <备份文件>"
    echo "  列出备份: $0 list"
    echo "  清理备份: $0 cleanup"
    echo "  查看信息: $0 info <备份文件>"
    echo "=========================================="
}

# 主函数
main() {
    local action="${1:-backup}"
    
    # 检查root权限
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0 [选项]"
        exit 1
    fi
    
    case $action in
        "backup")
            log_info "开始数据备份..."
            
            # 检查项目目录
            if [[ ! -d "$PROJECT_DIR" ]]; then
                log_error "项目目录不存在: $PROJECT_DIR"
                exit 1
            fi
            
            cd "$PROJECT_DIR"
            
            # 加载环境变量
            load_environment
            
            # 检查Docker服务
            if ! docker compose ps > /dev/null 2>&1; then
                log_error "Docker Compose服务未运行"
                exit 1
            fi
            
            create_backup_dir
            backup_postgres
            backup_redis
            backup_clickhouse
            backup_config
            create_backup_info
            compress_backup
            cleanup_old_backups
            show_backup_result
            
            log_success "数据备份完成！"
            ;;
        "restore")
            restore_data "$2"
            ;;
        "list")
            list_backups
            ;;
        "cleanup")
            cleanup_backups
            ;;
        "info")
            show_backup_info "$2"
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            log_error "未知操作: $action"
            show_usage
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
