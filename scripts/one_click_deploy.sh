#!/bin/bash
# 一键部署脚本 - 自动检测环境并选择部署方式
# 支持全新安装和升级迁移

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

# 显示欢迎信息
show_welcome() {
    clear
    echo -e "${PURPLE}"
    echo "=========================================="
    echo "    YK-VOS 一键部署脚本"
    echo "=========================================="
    echo -e "${NC}"
    echo "此脚本将自动检测您的环境并选择最适合的部署方式："
    echo "  • 全新安装：适用于新服务器"
    echo "  • 升级迁移：适用于已有数据的服务器"
    echo
    echo "支持的功能："
    echo "  ✓ VOS节点唯一UUID支持"
    echo "  ✓ 自动数据备份与恢复"
    echo "  ✓ 完整的服务管理"
    echo "  ✓ 健康检查与监控"
    echo
    echo "=========================================="
    echo
}

# 检查系统要求
check_system_requirements() {
    log_header "检查系统要求..."
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        log_error "不支持的操作系统"
        exit 1
    fi
    
    . /etc/os-release
    
    case "$ID" in
        ubuntu|debian|centos|rhel)
            log_success "支持的操作系统: $PRETTY_NAME"
            ;;
        *)
            log_error "不支持的操作系统: $ID"
            exit 1
            ;;
    esac
    
    # 检查内存
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $MEMORY_GB -lt 2 ]]; then
        log_warning "内存不足2GB，可能影响性能"
    else
        log_success "内存检查通过: ${MEMORY_GB}GB"
    fi
    
    # 检查磁盘空间
    DISK_GB=$(df / | awk 'NR==2{print int($4/1024/1024)}')
    if [[ $DISK_GB -lt 10 ]]; then
        log_error "磁盘空间不足10GB"
        exit 1
    else
        log_success "磁盘空间检查通过: ${DISK_GB}GB可用"
    fi
    
    # 检查网络连接
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        log_success "网络连接正常"
    else
        log_warning "网络连接异常，可能影响下载"
    fi
}

# 检测现有安装
detect_existing_installation() {
    log_header "检测现有安装..."
    
    PROJECT_DIR="/opt/yk-vos"
    
    if [[ -d "$PROJECT_DIR" ]]; then
        log_info "发现现有安装: $PROJECT_DIR"
        
        # 检查是否为有效安装
        if [[ -f "$PROJECT_DIR/docker-compose.yaml" ]]; then
            log_success "检测到有效的YK-VOS安装"
            return 0  # 存在有效安装
        else
            log_warning "发现不完整的安装，将进行全新安装"
            return 1  # 不存在有效安装
        fi
    else
        log_info "未发现现有安装，将进行全新安装"
        return 1  # 不存在安装
    fi
}

# 检查Docker安装
check_docker_installation() {
    log_header "检查Docker安装..."
    
    if command -v docker &> /dev/null && command -v docker compose &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        COMPOSE_VERSION=$(docker compose version --short)
        log_success "Docker已安装: $DOCKER_VERSION"
        log_success "Docker Compose已安装: $COMPOSE_VERSION"
        return 0
    else
        log_warning "Docker未安装，将在安装过程中自动安装"
        return 1
    fi
}

# 选择部署方式
select_deployment_method() {
    log_header "选择部署方式..."
    
    if detect_existing_installation; then
        echo "检测到现有安装，请选择操作："
        echo "1) 升级现有安装（保留数据）"
        echo "2) 全新安装（删除现有数据）"
        echo "3) 退出"
        echo
        
        while true; do
            read -p "请选择 (1-3): " choice
            case $choice in
                1)
                    DEPLOYMENT_METHOD="upgrade"
                    log_info "选择升级现有安装"
                    break
                    ;;
                2)
                    DEPLOYMENT_METHOD="fresh"
                    log_warning "选择全新安装（将删除现有数据）"
                    read -p "确认删除现有数据? (y/N): " -n 1 -r
                    echo
                    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                        log_info "取消操作"
                        exit 0
                    fi
                    break
                    ;;
                3)
                    log_info "退出安装"
                    exit 0
                    ;;
                *)
                    echo "无效选择，请输入1-3"
                    ;;
            esac
        done
    else
        DEPLOYMENT_METHOD="fresh"
        log_info "将进行全新安装"
    fi
}

# 执行部署
execute_deployment() {
    log_header "执行部署..."
    
    case $DEPLOYMENT_METHOD in
        "fresh")
            log_info "开始全新安装..."
            if [[ -f "scripts/fresh_install.sh" ]]; then
                chmod +x scripts/fresh_install.sh
                ./scripts/fresh_install.sh
            else
                log_error "未找到全新安装脚本"
                exit 1
            fi
            ;;
        "upgrade")
            log_info "开始升级安装..."
            if [[ -f "scripts/upgrade_migration.sh" ]]; then
                chmod +x scripts/upgrade_migration.sh
                ./scripts/upgrade_migration.sh
            else
                log_error "未找到升级脚本"
                exit 1
            fi
            ;;
        *)
            log_error "未知的部署方式: $DEPLOYMENT_METHOD"
            exit 1
            ;;
    esac
}

# 验证部署结果
verify_deployment() {
    log_header "验证部署结果..."
    
    PROJECT_DIR="/opt/yk-vos"
    cd "$PROJECT_DIR"
    
    # 检查服务状态
    log_info "检查服务状态..."
    if docker compose ps | grep -q "Up"; then
        log_success "所有服务运行正常"
    else
        log_error "部分服务运行异常"
        docker compose ps
        return 1
    fi
    
    # 检查前端访问
    log_info "检查前端服务..."
    if curl -s http://localhost:3000 > /dev/null; then
        log_success "前端服务正常"
    else
        log_warning "前端服务异常"
    fi
    
    # 检查后端API
    log_info "检查后端服务..."
    if curl -s http://localhost:3001/health > /dev/null; then
        log_success "后端服务正常"
    else
        log_warning "后端服务异常"
    fi
    
    # 检查数据库
    log_info "检查数据库连接..."
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
    
    if docker compose exec clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
        log_success "ClickHouse数据库正常"
    else
        log_warning "ClickHouse数据库异常"
    fi
}

# 显示部署结果
show_deployment_result() {
    log_header "部署完成！"
    
    echo
    echo "=========================================="
    echo "  YK-VOS 部署信息"
    echo "=========================================="
    echo "部署方式: $DEPLOYMENT_METHOD"
    echo "项目目录: /opt/yk-vos"
    echo "前端地址: http://$(hostname -I | awk '{print $1}'):3000"
    echo "后端地址: http://$(hostname -I | awk '{print $1}'):3001"
    echo
    echo "默认管理员账号:"
    echo "  用户名: admin"
    echo "  密码: admin123"
    echo "  (首次登录后请立即修改密码)"
    echo
    echo "服务管理命令:"
    echo "  查看状态: docker compose ps"
    echo "  查看日志: docker compose logs -f"
    echo "  重启服务: docker compose restart"
    echo "  停止服务: docker compose down"
    echo "  启动服务: docker compose up -d"
    echo
    echo "系统服务管理:"
    echo "  启动: sudo systemctl start yk-vos"
    echo "  停止: sudo systemctl stop yk-vos"
    echo "  状态: sudo systemctl status yk-vos"
    echo
    echo "新功能特性:"
    echo "  ✓ VOS节点唯一UUID支持"
    echo "  ✓ IP变更时数据关联连续性"
    echo "  ✓ 增强的网关同步功能"
    echo "  ✓ 改进的健康检查机制"
    echo "  ✓ 自动数据备份与恢复"
    echo
    echo "文档和支持:"
    echo "  部署指南: DEPLOYMENT_GUIDE.md"
    echo "  问题反馈: https://github.com/your-repo/yk-vos/issues"
    echo "=========================================="
    echo
}

# 创建快速管理脚本
create_management_scripts() {
    log_header "创建管理脚本..."
    
    PROJECT_DIR="/opt/yk-vos"
    
    # 创建快速管理脚本
    cat > /usr/local/bin/yk-vos << 'EOF'
#!/bin/bash
# YK-VOS 快速管理脚本

PROJECT_DIR="/opt/yk-vos"

case "$1" in
    "start")
        cd "$PROJECT_DIR" && docker compose up -d
        ;;
    "stop")
        cd "$PROJECT_DIR" && docker compose down
        ;;
    "restart")
        cd "$PROJECT_DIR" && docker compose restart
        ;;
    "status")
        cd "$PROJECT_DIR" && docker compose ps
        ;;
    "logs")
        cd "$PROJECT_DIR" && docker compose logs -f
        ;;
    "backup")
        cd "$PROJECT_DIR" && ./scripts/backup_data.sh
        ;;
    "update")
        cd "$PROJECT_DIR" && ./scripts/upgrade_migration.sh
        ;;
    *)
        echo "用法: yk-vos {start|stop|restart|status|logs|backup|update}"
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/yk-vos
    log_success "管理脚本创建完成: /usr/local/bin/yk-vos"
}

# 主函数
main() {
    show_welcome
    
    # 检查root权限
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
    
    check_system_requirements
    select_deployment_method
    execute_deployment
    verify_deployment
    create_management_scripts
    show_deployment_result
    
    log_success "部署完成！"
}

# 执行主函数
main "$@"
