#!/bin/bash
# 全新服务器初始化安装脚本
# 适用于没有现有数据的全新部署

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

# 检查系统要求
check_system() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        log_error "不支持的操作系统"
        exit 1
    fi
    
    . /etc/os-release
    
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" && "$ID" != "centos" && "$ID" != "rhel" ]]; then
        log_error "不支持的操作系统: $ID"
        exit 1
    fi
    
    log_success "操作系统检查通过: $PRETTY_NAME"
}

# 安装Docker和Docker Compose
install_docker() {
    log_info "安装Docker和Docker Compose..."
    
    if command -v docker &> /dev/null; then
        log_warning "Docker已安装，跳过安装步骤"
        return
    fi
    
    # 更新包管理器
    if [[ "$ID" == "ubuntu" || "$ID" == "debian" ]]; then
        apt-get update
        apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
        
        # 添加Docker官方GPG密钥
        curl -fsSL https://download.docker.com/linux/$ID/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # 添加Docker仓库
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$ID $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # 安装Docker
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        
    elif [[ "$ID" == "centos" || "$ID" == "rhel" ]]; then
        yum update -y
        yum install -y yum-utils
        
        # 添加Docker仓库
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        
        # 安装Docker
        yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    fi
    
    # 启动Docker服务
    systemctl start docker
    systemctl enable docker
    
    # 验证安装
    if docker --version && docker compose version; then
        log_success "Docker和Docker Compose安装成功"
    else
        log_error "Docker安装失败"
        exit 1
    fi
}

# 创建项目目录
create_project_dir() {
    log_info "创建项目目录..."
    
    PROJECT_DIR="/opt/yk-vos"
    
    if [[ -d "$PROJECT_DIR" ]]; then
        log_warning "项目目录已存在: $PROJECT_DIR"
        read -p "是否删除现有目录并重新创建? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
        else
            log_error "安装取消"
            exit 1
        fi
    fi
    
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    log_success "项目目录创建完成: $PROJECT_DIR"
}

# 下载项目代码
download_project() {
    log_info "下载项目代码..."
    
    # 检查git是否安装
    if ! command -v git &> /dev/null; then
        if [[ "$ID" == "ubuntu" || "$ID" == "debian" ]]; then
            apt-get install -y git
        elif [[ "$ID" == "centos" || "$ID" == "rhel" ]]; then
            yum install -y git
        fi
    fi
    
    # 克隆项目（这里假设有git仓库）
    # 如果没有git仓库，可以从压缩包解压
    if [[ -n "$GIT_REPO" ]]; then
        git clone "$GIT_REPO" .
    else
        log_warning "未指定Git仓库，请手动上传项目代码到 $PROJECT_DIR"
        log_info "或者设置环境变量 GIT_REPO 指定Git仓库地址"
        read -p "按回车键继续..."
    fi
    
    log_success "项目代码准备完成"
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."
    
    # 创建环境变量文件
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
    
    log_success "环境变量配置完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    # 启动数据库服务
    docker compose up -d postgres redis clickhouse
    
    # 等待数据库启动
    log_info "等待数据库启动..."
    sleep 30
    
    # 检查数据库连接
    if docker compose exec postgres pg_isready -U yk_vos_user -d yk_vos; then
        log_success "PostgreSQL数据库启动成功"
    else
        log_error "PostgreSQL数据库启动失败"
        exit 1
    fi
    
    # 执行数据库初始化脚本
    log_info "执行数据库初始化脚本..."
    
    # 基础表结构
    if [[ -f "sql/base.sql" ]]; then
        docker compose exec -T postgres psql -U yk_vos_user -d yk_vos < sql/base.sql
        log_success "基础表结构创建完成"
    fi
    
    # 初始化数据
    if [[ -f "sql/insert_user_agents.sql" ]]; then
        docker compose exec -T postgres psql -U yk_vos_user -d yk_vos < sql/insert_user_agents.sql
        log_success "初始数据插入完成"
    fi
    
    # ClickHouse初始化
    if [[ -f "clickhouse/init/01_create_tables.sql" ]]; then
        docker compose exec -T clickhouse clickhouse-client < clickhouse/init/01_create_tables.sql
        log_success "ClickHouse表结构创建完成"
    fi
    
    log_success "数据库初始化完成"
}

# 构建和启动应用
start_application() {
    log_info "构建和启动应用..."
    
    # 构建镜像
    docker compose build
    
    # 启动所有服务
    docker compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 60
    
    # 检查服务状态
    if docker compose ps | grep -q "Up"; then
        log_success "应用启动成功"
    else
        log_error "应用启动失败"
        docker compose logs
        exit 1
    fi
}

# 创建系统服务
create_systemd_service() {
    log_info "创建系统服务..."
    
    cat > /etc/systemd/system/yk-vos.service << EOF
[Unit]
Description=YK-VOS Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable yk-vos.service
    
    log_success "系统服务创建完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 检查防火墙类型
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian UFW
        ufw allow 3000/tcp
        ufw allow 3001/tcp
        log_success "UFW防火墙配置完成"
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL firewalld
        firewall-cmd --permanent --add-port=3000/tcp
        firewall-cmd --permanent --add-port=3001/tcp
        firewall-cmd --reload
        log_success "firewalld防火墙配置完成"
    else
        log_warning "未检测到防火墙，请手动开放端口 3000 和 3001"
    fi
}

# 显示安装结果
show_result() {
    log_success "安装完成！"
    echo
    echo "=========================================="
    echo "  YK-VOS 安装信息"
    echo "=========================================="
    echo "项目目录: $PROJECT_DIR"
    echo "前端地址: http://$(hostname -I | awk '{print $1}'):3000"
    echo "后端地址: http://$(hostname -I | awk '{print $1}'):3001"
    echo
    echo "管理命令:"
    echo "  启动服务: systemctl start yk-vos"
    echo "  停止服务: systemctl stop yk-vos"
    echo "  查看状态: systemctl status yk-vos"
    echo "  查看日志: docker compose logs -f"
    echo
    echo "数据库信息:"
    echo "  PostgreSQL: localhost:5432"
    echo "  Redis: localhost:6379"
    echo "  ClickHouse: localhost:8123"
    echo
    echo "默认管理员账号:"
    echo "  用户名: admin"
    echo "  密码: admin123"
    echo "  (首次登录后请立即修改密码)"
    echo "=========================================="
}

# 主函数
main() {
    log_info "开始全新安装 YK-VOS..."
    
    check_root
    check_system
    install_docker
    create_project_dir
    download_project
    setup_environment
    init_database
    start_application
    create_systemd_service
    configure_firewall
    show_result
    
    log_success "安装完成！"
}

# 执行主函数
main "$@"
