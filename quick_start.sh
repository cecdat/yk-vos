#!/bin/bash
# YK-VOS 一键启动脚本

set -e

echo "🎉 欢迎使用 YK-VOS v4 一键部署脚本"
echo "========================================="
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ 错误: Docker Compose 未安装"
    echo "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker 环境检查通过"
echo ""

# 检查环境变量文件
if [ ! -f "backend/.env" ]; then
    echo "📝 环境变量文件不存在，开始配置..."
    
    # 运行环境变量配置脚本
    if [ -f "setup_env.sh" ]; then
        bash setup_env.sh
    else
        echo "⚠️  警告: 找不到 setup_env.sh，请手动创建环境变量文件"
        echo "参考文档: ENV_SETUP.md"
        exit 1
    fi
else
    echo "✅ 环境变量文件已存在"
fi

echo ""
echo "🚀 开始构建并启动服务..."
echo ""

# 停止旧容器（如果存在）
echo "🧹 清理旧容器..."
docker-compose down 2>/dev/null || true

# 构建并启动
echo "🔨 构建镜像..."
docker-compose build

echo "▶️  启动服务..."
docker-compose up -d

echo ""
echo "⏳ 等待服务启动（约 30 秒）..."
sleep 10

# 检查服务状态
echo ""
echo "📊 检查服务状态..."
docker-compose ps

echo ""
echo "✅ 服务启动完成！"
echo ""
echo "========================================="
echo "📌 访问地址："
echo ""
echo "  🌐 前端界面: http://localhost:3000"
echo "  📚 API 文档: http://localhost:8000/docs"
echo "  ❤️  健康检查: http://localhost:8000/health"
echo ""
echo "========================================="
echo "🔑 默认账号："
echo ""
echo "  用户名: admin"
echo "  密码: Ykxx@2025"
echo ""
echo "  ⚠️  首次登录后请立即修改密码！"
echo ""
echo "========================================="
echo "📖 常用命令："
echo ""
echo "  查看日志:   docker-compose logs -f"
echo "  重启服务:   docker-compose restart"
echo "  停止服务:   docker-compose stop"
echo "  删除服务:   docker-compose down"
echo ""
echo "========================================="
echo ""
echo "🎉 部署完成！祝您使用愉快！"
echo ""

