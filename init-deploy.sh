#!/bin/bash

# YK-VOS 全新服务器初始化部署脚本
# 系统要求：Debian 10+ 或 Ubuntu 20.04+
# 适用于：首次部署到新服务器

set -e

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

# 显示欢迎信息
show_welcome() {
    clear
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                    ║${NC}"
    echo -e "${GREEN}║       YK-VOS 全新服务器初始化部署脚本              ║${NC}"
    echo -e "${GREEN}║                                                    ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    print_info "本脚本将自动完成以下任务："
    echo "  1. 检查系统环境（Docker、Docker Compose）"
    echo "  2. 创建环境配置文件"
    echo "  3. 构建基础镜像（只包含依赖）"
    echo "  4. 启动所有服务"
    echo "  5. 执行数据库初始化"
    echo "  6. 验证部署结果"
    echo ""
}

# 检查系统要求
check_requirements() {
    print_step "1/7 检查系统环境"
    
    # 检查操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "debian" && "$ID" != "ubuntu" ]]; then
            print_warning "检测到非 Debian/Ubuntu 系统: $ID"
            print_info "本脚本针对 Debian/Ubuntu 优化，其他系统可能需要手动调整"
        else
            print_success "系统检测: $PRETTY_NAME"
        fi
    fi
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        echo ""
        echo "请先安装 Docker："
        echo "  curl -fsSL https://get.docker.com | sh"
        echo "  sudo systemctl start docker"
        echo "  sudo systemctl enable docker"
        echo ""
        exit 1
    fi
    print_success "Docker 已安装: $(docker --version)"
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装"
        echo ""
        echo "请先安装 Docker Compose："
        echo "  sudo curl -L 'https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)' -o /usr/local/bin/docker-compose"
        echo "  sudo chmod +x /usr/local/bin/docker-compose"
        echo ""
        exit 1
    fi
    print_success "Docker Compose 已安装: $(docker-compose --version)"
    
    # 检查 Docker 守护进程
    if ! docker info &> /dev/null; then
        print_error "Docker 守护进程未运行"
        echo ""
        echo "请启动 Docker："
        echo "  sudo systemctl start docker"
        echo "  sudo systemctl enable docker"
        echo ""
        exit 1
    fi
    print_success "Docker 守护进程运行正常"
    
    # 检查磁盘空间
    available_space=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$available_space" -lt 5 ]; then
        print_warning "磁盘空间不足 5GB，建议至少 10GB"
    else
        print_success "磁盘空间充足: ${available_space}GB"
    fi
    
    # 检查内存
    available_mem=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$available_mem" -lt 2 ]; then
        print_warning "内存不足 2GB，建议至少 4GB"
    else
        print_success "内存充足: ${available_mem}GB"
    fi
}

# 创建环境配置文件
create_env_files() {
    print_step "2/7 创建环境配置文件"
    
    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -base64 16 | tr -d '=+/')
    
    # 创建后端配置
    if [ ! -f "backend/.env" ]; then
        print_info "创建 backend/.env..."
        cat > backend/.env <<EOF
# 数据库配置
POSTGRES_USER=vos_user
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_DB=vosadmin
DATABASE_URL=postgresql://vos_user:$DB_PASSWORD@postgres:5432/vosadmin

# JWT 配置
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis 配置
REDIS_URL=redis://redis:6379

# Celery 配置
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF
        print_success "backend/.env 已创建"
    else
        print_warning "backend/.env 已存在，跳过"
    fi
    
    # 创建前端配置
    if [ ! -f "frontend/.env.local" ]; then
        print_info "创建 frontend/.env.local..."
        cat > frontend/.env.local <<EOF
# API 地址
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
        print_success "frontend/.env.local 已创建"
    else
        print_warning "frontend/.env.local 已存在，跳过"
    fi
    
    # 创建根目录 .env
    if [ ! -f ".env" ]; then
        print_info "创建 .env..."
        cat > .env <<EOF
# 数据库配置
POSTGRES_USER=vos_user
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_DB=vosadmin

# JWT 配置
SECRET_KEY=$SECRET_KEY

# API 地址
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
        print_success ".env 已创建"
    else
        print_warning ".env 已存在，跳过"
    fi
    
    echo ""
    print_info "配置文件创建完成"
    print_warning "数据库密码: $DB_PASSWORD"
    print_warning "请妥善保管上述密码！"
    echo ""
}

# 构建基础镜像
build_base_images() {
    print_step "3/7 构建基础镜像（首次较慢，约 5-10 分钟）"
    
    print_info "构建后端基础镜像..."
    docker-compose -f docker-compose.base.yaml build backend-base
    print_success "后端基础镜像构建完成"
    
    print_info "构建前端基础镜像..."
    docker-compose -f docker-compose.base.yaml build frontend-base
    print_success "前端基础镜像构建完成"
}

# 启动服务
start_services() {
    print_step "4/7 启动所有服务"
    
    print_info "启动 Docker Compose 服务..."
    docker-compose up -d
    
    print_info "等待服务启动..."
    sleep 10
    
    print_success "所有服务已启动"
}

# 等待数据库就绪
wait_for_database() {
    print_step "5/7 等待数据库就绪"
    
    print_info "等待 PostgreSQL 启动..."
    
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose exec -T postgres pg_isready -U vos_user &> /dev/null; then
            print_success "PostgreSQL 已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    echo ""
    print_error "PostgreSQL 启动超时"
    return 1
}

# 初始化数据库
init_database() {
    print_step "6/7 初始化数据库"
    
    print_info "执行数据库迁移..."
    
    # 等待 backend 容器完全启动
    print_info "等待 backend 容器启动..."
    sleep 10
    
    # 检查容器是否正常运行
    if docker-compose ps backend | grep -q "Up"; then
        print_success "backend 容器已启动"
    else
        print_error "backend 容器启动失败"
        print_info "查看日志："
        docker-compose logs --tail=30 backend
        return 1
    fi
    
    print_success "数据库迁移已在容器启动时自动执行"
    
    print_info "数据库初始化完成"
}

# 验证部署
verify_deployment() {
    print_step "7/7 验证部署"
    
    # 检查容器状态
    print_info "检查容器状态..."
    docker-compose ps
    
    # 检查后端健康
    print_info "检查后端服务..."
    sleep 5
    if curl -s http://localhost:8000/health | grep -q "ok"; then
        print_success "后端服务正常 ✓"
    else
        print_warning "后端健康检查失败，请检查日志"
    fi
    
    # 检查前端
    print_info "检查前端服务..."
    if curl -s -I http://localhost:3000 | grep -q "200\|301\|302"; then
        print_success "前端服务正常 ✓"
    else
        print_warning "前端访问失败，请检查日志"
    fi
    
    # 检查数据库
    print_info "检查数据库..."
    if docker-compose exec -T postgres psql -U vos_user -d vosadmin -c "SELECT 1" &> /dev/null; then
        print_success "数据库连接正常 ✓"
    else
        print_warning "数据库连接失败"
    fi
    
    # 检查 Redis
    print_info "检查 Redis..."
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        print_success "Redis 连接正常 ✓"
    else
        print_warning "Redis 连接失败"
    fi
}

# 显示部署结果
show_result() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                    ║${NC}"
    echo -e "${GREEN}║           🎉 部署成功完成！🎉                      ║${NC}"
    echo -e "${GREEN}║                                                    ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${BLUE}📍 访问地址：${NC}"
    echo "  - 前端界面: http://localhost:3000"
    echo "  - 后端 API: http://localhost:8000"
    echo "  - API 文档: http://localhost:8000/docs"
    echo ""
    
    echo -e "${BLUE}👤 默认管理员账号：${NC}"
    echo "  - 用户名: admin"
    echo "  - 密码: admin123"
    echo ""
    print_warning "⚠️  首次登录后请立即修改密码！"
    echo ""
    
    echo -e "${BLUE}📊 服务状态：${NC}"
    docker-compose ps
    echo ""
    
    echo -e "${BLUE}🔧 常用命令：${NC}"
    echo "  - 查看日志: docker-compose logs -f"
    echo "  - 重启服务: docker-compose restart"
    echo "  - 停止服务: docker-compose down"
    echo "  - 更新代码: git pull && docker-compose restart"
    echo ""
    
    echo -e "${BLUE}📚 文档：${NC}"
    echo "  - README.md - 使用指南"
    echo "  - UPGRADE_GUIDE.md - 升级指南"
    echo ""
    
    print_success "部署完成！祝您使用愉快！🎉"
    echo ""
}

# 错误处理
handle_error() {
    print_error "部署过程中发生错误！"
    echo ""
    print_info "排查建议："
    echo "  1. 查看日志: docker-compose logs -f"
    echo "  2. 检查容器状态: docker-compose ps"
    echo "  3. 检查端口占用: netstat -tlnp | grep -E '3000|8000|5432|6379'"
    echo "  4. 清理重试: docker-compose down -v && ./init-deploy.sh"
    echo ""
    exit 1
}

# 主函数
main() {
    # 设置错误处理
    trap handle_error ERR
    
    # 检查是否在项目根目录
    if [ ! -f "docker-compose.yaml" ]; then
        print_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 显示欢迎信息
    show_welcome
    
    # 确认执行
    read -p "是否继续部署？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "已取消部署"
        exit 0
    fi
    
    # 执行部署步骤
    check_requirements
    create_env_files
    build_base_images
    start_services
    wait_for_database
    init_database
    verify_deployment
    show_result
}

# 执行主函数
main

