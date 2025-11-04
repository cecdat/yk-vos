#!/bin/bash
# 日常更新部署脚本 - 用于服务维护和健康检查
# 支持服务重启、健康检查、日志查看等功能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_header() {
    echo -e "${PURPLE}[HEADER]${NC} $1"
}

# 配置
PROJECT_DIR="/data/yk-vos"

# 显示使用说明
show_usage() {
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  restart         重启服务"
    echo "  health-check    健康检查（完成后显示系统信息）"
    echo "  logs            查看日志"
    echo "  status          查看状态（显示系统信息）"
    echo "  cleanup         清理系统"
    echo "  deploy          完整部署（重启服务+健康检查+系统信息）"
    echo "  info            显示系统信息（数据库信息、登录信息等）"
    echo
    echo "示例:"
    echo "  $0 restart        # 重启服务"
    echo "  $0 health-check   # 健康检查"
    echo "  $0 deploy         # 完整部署（不更新代码）"
    echo
    echo "注意: 此脚本不包含代码更新功能，如需更新代码请手动操作"
}

# 检查项目目录
check_project_dir() {
    if [[ ! -d "$PROJECT_DIR" ]]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    if [[ ! -f "docker-compose.yaml" ]]; then
        log_error "未找到 docker-compose.yaml 文件"
        exit 1
    fi
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

# 注意：代码更新功能已移除，日常维护脚本不负责代码更新
# 如需更新代码，请手动执行 git pull 或其他代码更新操作

# 重启服务
restart_services() {
    log_header "重启服务..."
    
    # 检查服务状态
    if docker compose ps | grep -q "Up"; then
        log_info "重启现有服务..."
        docker compose restart
    else
        log_info "启动服务..."
        docker compose up -d
    fi
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    if docker compose ps | grep -q "Up"; then
        log_success "服务重启成功"
    else
        log_error "服务重启失败"
        docker compose logs
        return 1
    fi
}

# 健康检查
health_check() {
    log_header "健康检查..."
    
    local all_healthy=true
    
    # 检查服务状态
    log_info "检查服务状态..."
    if docker compose ps | grep -q "Up"; then
        log_success "所有服务运行正常"
    else
        log_error "部分服务运行异常"
        all_healthy=false
    fi
    
    # 检查前端服务
    log_info "检查前端服务..."
    if curl -s http://localhost:3000 > /dev/null; then
        log_success "前端服务正常"
    else
        log_warning "前端服务异常"
        all_healthy=false
    fi
    
    # 检查后端API
    log_info "检查后端服务..."
    if curl -s http://localhost:3001/health > /dev/null; then
        log_success "后端服务正常"
    else
        log_warning "后端服务异常"
        all_healthy=false
    fi
    
    # 检查数据库
    log_info "检查数据库连接..."
    if docker compose exec postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
        log_success "PostgreSQL数据库正常"
    else
        log_warning "PostgreSQL数据库异常"
        all_healthy=false
    fi
    
    if docker compose exec redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis数据库正常"
    else
        log_warning "Redis数据库异常"
        all_healthy=false
    fi
    
    if docker compose exec clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
        log_success "ClickHouse数据库正常"
    else
        log_warning "ClickHouse数据库异常"
        all_healthy=false
    fi
    
    # 检查磁盘空间
    log_info "检查磁盘空间..."
    local disk_usage=$(df / | awk 'NR==2{print int($5)}')
    if [[ $disk_usage -lt 80 ]]; then
        log_success "磁盘空间正常: ${disk_usage}%"
    else
        log_warning "磁盘空间不足: ${disk_usage}%"
        all_healthy=false
    fi
    
    # 检查内存使用
    log_info "检查内存使用..."
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [[ $memory_usage -lt 90 ]]; then
        log_success "内存使用正常: ${memory_usage}%"
    else
        log_warning "内存使用过高: ${memory_usage}%"
        all_healthy=false
    fi
    
    if [[ "$all_healthy" == "true" ]]; then
        log_success "所有健康检查通过"
    else
        log_warning "部分健康检查失败"
    fi
}

# 查看日志
view_logs() {
    log_header "查看日志..."
    
    echo "选择要查看的日志:"
    echo "1) 所有服务日志"
    echo "2) 后端服务日志"
    echo "3) 前端服务日志"
    echo "4) 数据库日志"
    echo "5) 系统日志"
    echo
    
    read -p "请选择 (1-5): " choice
    
    case $choice in
        1)
            docker compose logs -f
            ;;
        2)
            docker compose logs -f backend
            ;;
        3)
            docker compose logs -f frontend
            ;;
        4)
            docker compose logs -f postgres redis clickhouse
            ;;
        5)
            journalctl -u yk-vos -f
            ;;
        *)
            log_error "无效选择"
            ;;
    esac
}

# 查看状态
view_status() {
    log_header "服务状态..."
    
    echo "=========================================="
    echo "  YK-VOS 服务状态"
    echo "=========================================="
    echo
    
    # 服务状态
    echo "服务状态:"
    docker compose ps
    echo
    
    # 资源使用
    echo "资源使用:"
    docker stats --no-stream
    echo
    
    # 磁盘使用
    echo "磁盘使用:"
    df -h
    echo
    
    # 内存使用
    echo "内存使用:"
    free -h
    echo
    
    # 网络连接
    echo "网络连接:"
    netstat -tlnp | grep -E ":(3000|3001|5432|6379|8123)"
    echo
    
    echo "=========================================="
}

# 清理系统
cleanup_system() {
    log_header "清理系统..."
    
    # 清理Docker无用数据
    log_info "清理Docker无用数据..."
    docker system prune -f
    
    # 清理无用的镜像
    log_info "清理无用的镜像..."
    docker image prune -f
    
    # 清理无用的容器
    log_info "清理无用的容器..."
    docker container prune -f
    
    # 清理无用的网络
    log_info "清理无用的网络..."
    docker network prune -f
    
    # 清理无用的卷
    log_info "清理无用的卷..."
    docker volume prune -f
    
    # 清理日志文件
    log_info "清理日志文件..."
    find /var/log -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    # 清理临时文件
    log_info "清理临时文件..."
    find /tmp -type f -mtime +7 -delete 2>/dev/null || true
    
    log_success "系统清理完成"
}

# 显示系统信息
show_system_info() {
    # 读取环境变量
    if [[ -f ".env" ]]; then
        source .env
    fi
    
    # 获取服务器IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    if [[ -z "$SERVER_IP" ]]; then
        SERVER_IP="localhost"
    fi
    
    # 获取数据库配置（从.env文件或使用默认值）
    PG_USER=${POSTGRES_USER:-"vos_user"}
    PG_DB=${POSTGRES_DB:-"vosadmin"}
    PG_PASSWORD=${POSTGRES_PASSWORD:-"Ykxx@2025"}
    CH_USER=${CLICKHOUSE_USER:-"vosadmin"}
    CH_PASSWORD=${CLICKHOUSE_PASSWORD:-"Ykxx@2025"}
    CH_DB=${CLICKHOUSE_DB:-"vos_cdrs"}
    
    echo
    echo "=========================================="
    echo "  YK-VOS 系统信息"
    echo "=========================================="
    echo
    echo "📍 访问地址:"
    echo "  前端界面: http://$SERVER_IP:3000"
    echo "  后端API:  http://$SERVER_IP:3001"
    echo "  API文档:  http://$SERVER_IP:3001/docs"
    echo
    echo "🔐 登录信息:"
    echo "  用户名: admin"
    echo "  密码:   admin123"
    echo "  ⚠️  首次登录后请立即修改密码！"
    echo
    echo "🗄️  数据库信息:"
    echo "  PostgreSQL:"
    echo "    地址:   $SERVER_IP:5430 (容器内: postgres:5432)"
    echo "    数据库: $PG_DB"
    echo "    用户名: $PG_USER"
    echo "    密码:   $PG_PASSWORD"
    echo
    echo "  ClickHouse:"
    echo "    HTTP端口:  $SERVER_IP:8123"
    echo "    Native端口: $SERVER_IP:9000"
    echo "    数据库:   $CH_DB"
    echo "    用户名:   $CH_USER"
    echo "    密码:     $CH_PASSWORD"
    echo
    echo "  Redis:"
    echo "    地址:   $SERVER_IP:6379 (容器内: redis:6379)"
    echo
    echo "💻 管理命令:"
    echo "  启动服务: systemctl start yk-vos"
    echo "  停止服务: systemctl stop yk-vos"
    echo "  查看状态: systemctl status yk-vos"
    echo "  查看日志: docker compose logs -f"
    echo
    echo "🔧 日常维护:"
    echo "  日常更新: bash scripts/daily_update.sh"
    echo "  数据备份: bash scripts/backup_data.sh"
    echo "  健康检查: bash scripts/daily_update.sh health-check"
    echo
    echo "📝 项目目录: $PROJECT_DIR"
    echo "   配置文件: $PROJECT_DIR/.env"
    echo "   数据目录: $PROJECT_DIR/data/"
    echo
    echo "=========================================="
    echo
}

# 完整部署流程（不包含代码更新）
deploy_all() {
    log_header "开始完整部署流程..."
    
    log_info "注意: 此脚本不包含代码更新功能，请确保代码已是最新版本"
    
    # 1. 重启服务
    if restart_services; then
        log_success "服务重启完成"
    else
        log_error "服务重启失败"
        return 1
    fi
    
    # 2. 健康检查
    health_check
    
    log_success "完整部署流程完成"
    
    # 3. 显示系统信息
    show_system_info
}

# 主函数
main() {
    local action="${1:-deploy}"
    
    # 检查root权限
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0 [选项]"
        exit 1
    fi
    
    check_project_dir
    load_environment
    
    case $action in
        "restart")
            restart_services
            ;;
        "health-check")
            health_check
            show_system_info
            ;;
        "logs")
            view_logs
            ;;
        "status")
            view_status
            show_system_info
            ;;
        "cleanup")
            cleanup_system
            ;;
        "deploy")
            deploy_all
            ;;
        "info")
            show_system_info
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
