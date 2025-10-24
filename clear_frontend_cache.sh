#!/bin/bash

echo "🧹 清理前端缓存并重启"

echo ""
echo "1️⃣ 停止前端容器..."
docker-compose stop frontend

echo ""
echo "2️⃣ 清理 Next.js 编译缓存..."
# 删除 .next 目录（编译缓存）
docker-compose run --rm frontend sh -c "rm -rf /usr/src/app/.next"

echo ""
echo "3️⃣ 查看当前环境变量..."
echo "NEXT_PUBLIC_API_BASE 应该是: /api/v1"
echo "BACKEND_API_URL 应该是: http://backend:8000"
cat docker-compose.yaml | grep -A 3 "NEXT_PUBLIC_API_BASE"

echo ""
echo "4️⃣ 启动前端容器（会重新编译）..."
docker-compose up -d frontend

echo ""
echo "5️⃣ 等待前端启动（30秒）..."
sleep 30

echo ""
echo "6️⃣ 查看前端日志..."
docker-compose logs frontend --tail=20

echo ""
echo "7️⃣ 验证环境变量..."
docker-compose exec frontend env | grep -E "NEXT_PUBLIC_API_BASE|BACKEND_API_URL"

echo ""
echo "✅ 清理完成！"
echo ""
echo "📋 接下来请："
echo "  1. 清除浏览器缓存（Ctrl+Shift+Delete）"
echo "  2. 关闭浏览器标签"
echo "  3. 重新打开 http://服务器IP:3000/login"
echo "  4. 打开F12开发者工具，查看Network标签"
echo "  5. 尝试登录，查看请求的URL应该是: http://服务器IP:3000/api/v1/auth/login"

