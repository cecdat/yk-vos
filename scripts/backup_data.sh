#!/bin/bash
# 数据备份脚本
# 用于备份YK-VOS的所有数据

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
BACKUP_BASE_DIR="/opt/yk-vos-backups"
BACKUP_DIR="$BACKUP_BASE_DIR/backup-$(date +%Y%m%d-%H%M%S)"

# 创建备份目录
create_backup_dir() {
    log_info "创建备份目录: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
}

# 备份PostgreSQL数据库
backup_postgres() {
    log_info "备份PostgreSQL数据库..."
    
    if docker compose exec postgres pg_isready -U yk_vos_user -d yk_vos > /dev/null 2>&1; then
        docker compose exec -T postgres pg_dump -U yk_vos_user yk_vos > "$BACKUP_DIR/postgres_backup.sql"
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
    echo "恢复命令:"
    echo "  ./scripts/restore_data.sh <备份文件>"
    echo "=========================================="
}

# 主函数
main() {
    log_info "开始数据备份..."
    
    # 检查项目目录
    if [[ ! -d "$PROJECT_DIR" ]]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
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
}

# 执行主函数
main "$@"
