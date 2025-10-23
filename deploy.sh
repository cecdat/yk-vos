#!/bin/bash

# YK-VOS 一键部署/更新脚本
# 适用于：代码更新后的快速部署
# 使用方法：bash deploy.sh

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 显示菜单
show_menu() {
    clear
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                ║${NC}"
    echo -e "${GREEN}║        YK-VOS 部署工具                         ║${NC}"
    echo -e "${GREEN}║                                                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "请选择操作："
    echo ""
    echo "  1) 快速更新 (拉代码 + 重启服务)"
    echo "  2) 完整升级 (备份 + 拉代码 + 迁移 + 重启)"
    echo "  3) 仅重启服务"
    echo "  4) 查看服务状态"
    echo "  5) 查看日志"
    echo "  0) 退出"
    echo ""
    echo -n "请输入选项 [0-5]: "
}

# 快速更新
quick_update() {
    echo ""
    echo -e "${BLUE}━━━ 快速更新 ━━━${NC}"
    
    # 拉取代码
    if [ -d ".git" ]; then
        echo "📥 拉取最新代码..."
        git pull
        echo -e "${GREEN}✓${NC} 代码已更新"
    fi
    
    # 重启服务
    echo "🔄 重启服务..."
    docker-compose restart backend frontend celery-worker celery-beat
    echo -e "${GREEN}✓${NC} 服务已重启"
    
    # 等待启动
    echo "⏳ 等待服务启动..."
    sleep 5
    
    # 健康检查
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} 后端服务正常"
    fi
    
    if curl -s -I http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} 前端服务正常"
    fi
    
    echo ""
    echo -e "${GREEN}✅ 快速更新完成！${NC}"
}

# 完整升级
full_upgrade() {
    echo ""
    echo -e "${BLUE}━━━ 完整升级 ━━━${NC}"
    echo ""
    echo "⚠️  这将执行："
    echo "  • 备份数据库"
    echo "  • 拉取最新代码"
    echo "  • 执行数据库迁移"
    echo "  • 重启所有服务"
    echo ""
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        return
    fi
    
    bash upgrade.sh
}

# 仅重启服务
restart_services() {
    echo ""
    echo -e "${BLUE}━━━ 重启服务 ━━━${NC}"
    docker-compose restart
    echo -e "${GREEN}✓${NC} 所有服务已重启"
    sleep 3
    docker-compose ps
}

# 查看状态
show_status() {
    echo ""
    echo -e "${BLUE}━━━ 服务状态 ━━━${NC}"
    docker-compose ps
    echo ""
    
    # 健康检查
    echo "🔍 健康检查："
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "  后端: ${GREEN}✓ 正常${NC}"
    else
        echo -e "  后端: ${RED}✗ 异常${NC}"
    fi
    
    if curl -s -I http://localhost:3000 > /dev/null 2>&1; then
        echo -e "  前端: ${GREEN}✓ 正常${NC}"
    else
        echo -e "  前端: ${RED}✗ 异常${NC}"
    fi
    
    if docker-compose exec -T postgres pg_isready -U vos_user > /dev/null 2>&1; then
        echo -e "  数据库: ${GREEN}✓ 正常${NC}"
    else
        echo -e "  数据库: ${RED}✗ 异常${NC}"
    fi
    
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "  Redis: ${GREEN}✓ 正常${NC}"
    else
        echo -e "  Redis: ${RED}✗ 异常${NC}"
    fi
}

# 查看日志
show_logs() {
    echo ""
    echo -e "${BLUE}━━━ 服务日志 ━━━${NC}"
    echo ""
    echo "选择要查看的服务日志："
    echo "  1) 后端"
    echo "  2) 前端"
    echo "  3) Celery Worker"
    echo "  4) Celery Beat"
    echo "  5) 所有服务"
    echo ""
    read -p "请输入选项 [1-5]: " log_choice
    
    case $log_choice in
        1) docker-compose logs -f backend ;;
        2) docker-compose logs -f frontend ;;
        3) docker-compose logs -f celery-worker ;;
        4) docker-compose logs -f celery-beat ;;
        5) docker-compose logs -f ;;
        *) echo "无效选项" ;;
    esac
}

# 主循环
main() {
    while true; do
        show_menu
        read choice
        
        case $choice in
            1) quick_update; read -p "按回车继续..." ;;
            2) full_upgrade; read -p "按回车继续..." ;;
            3) restart_services; read -p "按回车继续..." ;;
            4) show_status; read -p "按回车继续..." ;;
            5) show_logs ;;
            0) echo ""; echo "再见！"; exit 0 ;;
            *) echo ""; echo -e "${RED}无效选项，请重试${NC}"; sleep 2 ;;
        esac
    done
}

# 运行主函数
main

