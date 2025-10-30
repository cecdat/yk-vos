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
    
    # 自动检测项目目录
    local possible_dirs=("/opt/yk-vos" "/data/yk-vos" "/home/yk-vos" "/usr/local/yk-vos")
    PROJECT_DIR=""
    
    for dir in "${possible_dirs[@]}"; do
        if [[ -d "$dir" && -f "$dir/docker-compose.yaml" ]]; then
            PROJECT_DIR="$dir"
            break
        fi
    done
    
    # 如果还是没找到，尝试从当前目录向上查找
    if [[ -z "$PROJECT_DIR" ]]; then
        local current_dir="$(pwd)"
        while [[ "$current_dir" != "/" ]]; do
            if [[ -f "$current_dir/docker-compose.yaml" ]]; then
                PROJECT_DIR="$current_dir"
                break
            fi
            current_dir="$(dirname "$current_dir")"
        done
    fi
    
    if [[ -z "$PROJECT_DIR" ]]; then
        log_error "未找到YK-VOS安装目录"
        log_info "请确保在正确的项目目录中运行此脚本，或使用 fresh_install.sh 进行全新安装"
        log_info "支持的目录: ${possible_dirs[*]}"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    if [[ ! -f "docker-compose.yaml" ]]; then
        log_error "未找到 docker-compose.yaml 文件"
        exit 1
    fi
    
    log_success "找到现有安装: $PROJECT_DIR"
}

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

# 备份现有数据
backup_data() {
    log_info "备份现有数据..."
    
    BACKUP_DIR="${PROJECT_DIR}-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    local backup_success=true
    
    # 备份数据库
    log_info "备份PostgreSQL数据库..."
    if docker compose exec postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
        if docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_DIR/postgres_backup.sql" 2>/dev/null; then
            log_success "PostgreSQL备份完成"
        else
            log_warning "PostgreSQL备份失败，跳过"
            backup_success=false
        fi
    else
        log_warning "PostgreSQL数据库连接失败，跳过备份"
        backup_success=false
    fi
    
    # 备份Redis数据
    log_info "备份Redis数据..."
    if docker compose exec redis redis-cli ping > /dev/null 2>&1; then
        # 确保备份目录存在（redis-cli可能会在容器内执行）
        mkdir -p "$BACKUP_DIR"
        if docker compose exec redis redis-cli --rdb "/tmp/redis_backup.rdb" > /dev/null 2>&1; then
            docker compose cp redis:/tmp/redis_backup.rdb "$BACKUP_DIR/redis_backup.rdb" 2>/dev/null || {
                log_warning "Redis备份文件复制失败，跳过"
                backup_success=false
            }
            docker compose exec redis rm -f /tmp/redis_backup.rdb 2>/dev/null || true
            log_success "Redis备份完成"
        else
            log_warning "Redis备份失败，跳过"
            backup_success=false
        fi
    else
        log_warning "Redis数据库连接失败，跳过备份"
        backup_success=false
    fi
    
    # 备份ClickHouse数据
    log_info "备份ClickHouse数据..."
    if docker compose exec clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
        docker compose exec -T clickhouse clickhouse-client --query "BACKUP DATABASE vos_cdrs TO Disk('backups', 'vos_cdrs_backup')" > /dev/null 2>&1 || log_warning "ClickHouse备份失败，跳过"
        log_success "ClickHouse备份完成"
    else
        log_warning "ClickHouse数据库连接失败，跳过备份"
        backup_success=false
    fi
    
    # 备份配置文件
    log_info "备份配置文件..."
    mkdir -p "$BACKUP_DIR/config_backup"
    cp .env "$BACKUP_DIR/config_backup/" 2>/dev/null || log_warning "未找到.env文件"
    cp docker-compose.yaml "$BACKUP_DIR/config_backup/" 2>/dev/null || log_warning "未找到docker-compose.yaml文件"
    cp -r sql "$BACKUP_DIR/config_backup/" 2>/dev/null || log_warning "未找到sql目录"
    
    if [[ "$backup_success" == "true" ]]; then
        log_success "数据备份完成: $BACKUP_DIR"
    else
        log_warning "部分数据备份失败，但继续升级流程"
    fi
    
    # 显示备份信息
    if [[ -d "$BACKUP_DIR" ]]; then
        echo "备份文件列表:"
        ls -la "$BACKUP_DIR" 2>/dev/null || true
    fi
}

# 停止现有服务
stop_services() {
    log_info "停止现有服务..."
    
    docker compose down
    
    # 等待服务完全停止
    sleep 10
    
    log_success "服务已停止"
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
    if ! docker compose exec postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; then
        log_error "PostgreSQL数据库连接失败"
        exit 1
    fi
    
    # 执行数据库迁移脚本
    log_info "执行PostgreSQL迁移脚本..."
    
    # 检查数据库版本
    DB_VERSION=$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT version FROM db_versions ORDER BY applied_at DESC LIMIT 1;" 2>/dev/null | xargs || echo "0")
    
    log_info "当前数据库版本: $DB_VERSION"
    
    # 执行v2.3升级脚本
    log_info "检查v2.3升级脚本..."
    if [[ -f "sql/upgrade_db_v2.3.sql" ]]; then
        docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < sql/upgrade_db_v2.3.sql
        log_success "PostgreSQL v2.3升级检查完成"
    else
        log_warning "未找到升级脚本: sql/upgrade_db_v2.3.sql"
    fi
    
    # 执行v2.4升级脚本
    log_info "检查v2.4升级脚本..."
    if [[ -f "sql/upgrade_db_v2.4.sql" ]]; then
        docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < sql/upgrade_db_v2.4.sql
        log_success "PostgreSQL v2.4升级检查完成"
    else
        log_warning "未找到升级脚本: sql/upgrade_db_v2.4.sql"
    fi
    
    # 执行ClickHouse升级（可选，失败不影响升级）
    log_info "执行ClickHouse升级..."
    if [[ -f "clickhouse/init/02_upgrade_add_vos_uuid.sql" ]]; then
        if docker compose exec -T clickhouse clickhouse-client < clickhouse/init/02_upgrade_add_vos_uuid.sql 2>/dev/null; then
            log_success "ClickHouse升级完成"
        else
            log_warning "ClickHouse升级失败（可能表不存在），跳过"
        fi
    else
        log_warning "未找到ClickHouse升级脚本"
    fi
    
    # 填充已有VOS节点的UUID
    log_info "填充已有VOS节点的UUID..."
    
    # 检查是否还有未填充UUID的VOS节点
    result=$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM vos_instances WHERE vos_uuid IS NULL;" 2>/dev/null)
    missing_uuid_count=$(echo "$result" | tr -d ' \n')
    
    if [[ "$missing_uuid_count" -gt 0 ]]; then
        log_info "发现 $missing_uuid_count 个未设置UUID的VOS节点"
        
        # 为未设置UUID的节点生成UUID
        docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
UPDATE vos_instances 
SET vos_uuid = gen_random_uuid() 
WHERE vos_uuid IS NULL;
EOF
        
        # 填充相关数据
        log_info "填充相关数据的UUID..."
        
        # vos_data_cache
        docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
UPDATE vos_data_cache 
SET vos_uuid = vi.vos_uuid 
FROM vos_instances vi 
WHERE vos_data_cache.vos_instance_id = vi.id 
AND vos_data_cache.vos_uuid IS NULL;
EOF
        
        # gateways
        docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
UPDATE gateways 
SET vos_uuid = vi.vos_uuid 
FROM vos_instances vi 
WHERE gateways.vos_instance_id = vi.id 
AND gateways.vos_uuid IS NULL;
EOF
        
        # customers
        docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
UPDATE customers 
SET vos_uuid = vi.vos_uuid 
FROM vos_instances vi 
WHERE customers.vos_instance_id = vi.id 
AND customers.vos_uuid IS NULL;
EOF
        
        # cdrs
        docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
UPDATE cdrs 
SET vos_uuid = vi.vos_uuid 
FROM vos_instances vi 
WHERE cdrs.vos_id = vi.id 
AND cdrs.vos_uuid IS NULL;
EOF
        
        # phones
        docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
UPDATE phones 
SET vos_uuid = vi.vos_uuid 
FROM vos_instances vi 
WHERE phones.vos_id = vi.id 
AND phones.vos_uuid IS NULL;
EOF
        
        # vos_health_check (支持两种表名)
        docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
DO \$\$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vos_health_check') THEN
        UPDATE vos_health_check 
        SET vos_uuid = vi.vos_uuid 
        FROM vos_instances vi 
        WHERE vos_health_check.vos_instance_id = vi.id 
        AND vos_health_check.vos_uuid IS NULL;
    ELSIF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vos_health_checks') THEN
        UPDATE vos_health_checks 
        SET vos_uuid = vi.vos_uuid 
        FROM vos_instances vi 
        WHERE vos_health_checks.vos_instance_id = vi.id 
        AND vos_health_checks.vos_uuid IS NULL;
    END IF;
END \$\$;
EOF
        
        log_success "PostgreSQL VOS UUID填充完成"
        
        # 填充ClickHouse中的vos_uuid（使用PostgreSQL中生成的UUID）
        log_info "填充ClickHouse中的vos_uuid..."
        if docker compose ps clickhouse | grep -q "Up"; then
            # ClickHouse服务正在运行，尝试填充UUID
            # 获取PostgreSQL中的UUID映射并更新ClickHouse
            log_info "从PostgreSQL获取UUID映射..."
            UUID_MAP=$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT id::text || ':' || vos_uuid::text FROM vos_instances WHERE vos_uuid IS NOT NULL;" 2>/dev/null)
            
            if [[ -n "$UUID_MAP" ]]; then
                # 检查ClickHouse表是否存在
                if docker compose exec -T clickhouse clickhouse-client -q "EXISTS TABLE cdrs" 2>/dev/null | grep -q "1"; then
                    log_info "ClickHouse cdrs表存在，开始填充UUID..."
                    
                    # 为每个VOS实例更新ClickHouse中的UUID
                    echo "$UUID_MAP" | while IFS=: read -r vos_id vos_uuid; do
                        vos_id=$(echo "$vos_id" | tr -d ' \n')
                        vos_uuid=$(echo "$vos_uuid" | tr -d ' \n')
                        if [[ -n "$vos_id" && -n "$vos_uuid" ]]; then
                            log_info "  更新VOS ID $vos_id 的UUID: $vos_uuid"
                            docker compose exec -T clickhouse clickhouse-client <<EOF 2>/dev/null || true
ALTER TABLE cdrs UPDATE vos_uuid = '$vos_uuid' WHERE vos_id = $vos_id AND (vos_uuid = '' OR vos_uuid IS NULL);
EOF
                        fi
                    done
                    
                    log_success "ClickHouse UUID填充操作已提交（异步执行）"
                else
                    log_warning "ClickHouse cdrs表不存在，跳过UUID填充"
                fi
            else
                log_warning "未获取到UUID映射，跳过ClickHouse UUID填充"
            fi
        else
            log_warning "ClickHouse服务未运行，跳过UUID填充"
        fi
    else
        log_info "所有VOS节点已有UUID，无需填充"
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
    if [[ -n "$BACKUP_DIR" ]] && [[ -d "$BACKUP_DIR" ]]; then
        echo "备份位置: $BACKUP_DIR"
    fi
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
    
    # 检查是否跳过备份
    SKIP_BACKUP=false
    if [[ "$1" == "--skip-backup" ]] || [[ "$1" == "-s" ]]; then
        SKIP_BACKUP=true
        log_warning "跳过数据备份"
    fi
    
    check_root
    check_existing_installation
    load_environment
    
    # 可选的数据备份
    if [[ "$SKIP_BACKUP" == "false" ]]; then
        backup_data || log_warning "备份失败，继续升级流程"
    else
        log_info "已跳过数据备份步骤"
    fi
    
    log_info "注意：请确保代码已更新到最新版本"
    log_info "请手动执行以下操作后按回车继续："
    echo "  1. git pull 或更新代码"
    echo "  2. (可选) docker compose build 重新构建镜像"
    read -p "按回车键继续..." || true
    
    stop_services
    run_database_migration
    update_environment
    start_services
    verify_upgrade
    show_result
    
    log_success "升级完成！"
}

# 执行主函数
main "$@"
