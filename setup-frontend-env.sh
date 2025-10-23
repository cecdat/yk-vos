#!/bin/bash
# 配置前端 API 地址脚本

echo "========================================"
echo "🔧 配置前端 API 地址"
echo "========================================"
echo ""

# 获取服务器 IP
read -p "请输入服务器 IP 地址或域名 (例如: 192.168.1.100 或 yourdomain.com): " SERVER_ADDR

if [ -z "$SERVER_ADDR" ]; then
    echo "❌ 错误: 未输入服务器地址"
    exit 1
fi

# 选择协议
read -p "使用 HTTPS? (y/N): " USE_HTTPS
if [[ $USE_HTTPS =~ ^[Yy]$ ]]; then
    PROTOCOL="https"
else
    PROTOCOL="http"
fi

# 设置端口
read -p "后端端口 (默认: 8000): " BACKEND_PORT
BACKEND_PORT=${BACKEND_PORT:-8000}

# 构建 API URL
API_BASE_URL="${PROTOCOL}://${SERVER_ADDR}:${BACKEND_PORT}/api/v1"

echo ""
echo "📋 配置信息："
echo "  服务器地址: $SERVER_ADDR"
echo "  协议: $PROTOCOL"
echo "  后端端口: $BACKEND_PORT"
echo "  API 基础 URL: $API_BASE_URL"
echo ""

read -p "确认配置? (Y/n): " CONFIRM
if [[ ! $CONFIRM =~ ^[Yy]?$ ]]; then
    echo "❌ 已取消"
    exit 0
fi

# 更新 docker-compose.yaml
echo ""
echo "📝 更新 docker-compose.yaml..."

# 使用临时文件进行替换
TMP_FILE=$(mktemp)

# 读取并更新配置
awk -v api_url="$API_BASE_URL" '
/NEXT_PUBLIC_API_BASE:/ {
    print "      NEXT_PUBLIC_API_BASE: " api_url
    next
}
{ print }
' docker-compose.yaml > "$TMP_FILE"

# 替换原文件
mv "$TMP_FILE" docker-compose.yaml

echo "✅ 配置已更新"
echo ""
echo "🚀 重启前端容器..."
docker-compose restart frontend

echo ""
echo "========================================"
echo "✅ 配置完成！"
echo "========================================"
echo ""
echo "🌐 访问地址："
echo "  前端: http://$SERVER_ADDR:3000"
echo "  后端 API: $API_BASE_URL"
echo ""
echo "💡 提示："
echo "  1. 打开浏览器访问 http://$SERVER_ADDR:3000"
echo "  2. 使用默认账户登录："
echo "     用户名: admin"
echo "     密码: admin123"
echo ""

