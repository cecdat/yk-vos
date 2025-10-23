#!/bin/bash
# 重新构建并部署脚本（修复数据库配置问题）

set -e

echo "========================================"
echo "🔧 重新构建并部署 YK-VOS"
echo "========================================"
echo ""

# 停止所有容器
echo "📋 步骤 1: 停止所有容器"
echo "----------------------------------------"
docker-compose down
echo "✅ 容器已停止"
echo ""

# 清理旧的数据库数据（可选，如果需要保留数据请跳过）
read -p "是否清理旧的数据库数据？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📋 步骤 2: 清理数据库数据"
    echo "----------------------------------------"
    rm -rf data/postgres
    mkdir -p data/postgres
    echo "✅ 数据库数据已清理"
else
    echo "📋 步骤 2: 保留现有数据库数据"
    echo "----------------------------------------"
    echo "⚠️  跳过数据清理"
fi
echo ""

# 重新构建基础镜像
echo "📋 步骤 3: 重新构建基础镜像"
echo "----------------------------------------"
echo "这可能需要几分钟时间..."
docker-compose -f docker-compose.base.yaml build --no-cache
echo "✅ 基础镜像构建完成"
echo ""

# 启动所有服务
echo "📋 步骤 4: 启动所有服务"
echo "----------------------------------------"
docker-compose up -d
echo "✅ 服务已启动"
echo ""

# 等待服务启动
echo "📋 步骤 5: 等待服务启动"
echo "----------------------------------------"
echo "等待 30 秒..."
sleep 30
echo ""

# 检查服务状态
echo "📋 步骤 6: 检查服务状态"
echo "----------------------------------------"
docker-compose ps
echo ""

# 查看后端日志
echo "📋 步骤 7: 后端日志（最近 30 行）"
echo "----------------------------------------"
docker-compose logs --tail=30 backend
echo ""

# 检查数据库连接
echo "📋 步骤 8: 验证数据库"
echo "----------------------------------------"
echo "检查数据库连接..."
if docker-compose exec postgres psql -U vos_user -d vosadmin -c "SELECT 'Database OK' as status;" 2>/dev/null; then
    echo "✅ 数据库连接成功"
    echo ""
    echo "查看数据库表..."
    docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt"
else
    echo "❌ 数据库连接失败"
fi
echo ""

echo "========================================"
echo "✅ 部署完成！"
echo "========================================"
echo ""
echo "🌐 访问地址："
echo "   前端: http://your-server:3000"
echo "   后端: http://your-server:8000"
echo ""
echo "🔑 默认管理员账户："
echo "   用户名: admin"
echo "   密码: admin123"
echo ""
echo "📊 查看实时日志："
echo "   docker-compose logs -f backend"
echo ""

