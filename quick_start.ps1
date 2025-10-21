# YK-VOS 一键启动脚本 (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "🎉 欢迎使用 YK-VOS v4 一键部署脚本" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker
try {
    docker --version | Out-Null
    Write-Host "✅ Docker 环境检查通过" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: Docker 未安装" -ForegroundColor Red
    Write-Host "请先安装 Docker Desktop: https://docs.docker.com/desktop/install/windows-install/"
    exit 1
}

# 检查 Docker Compose
try {
    docker-compose --version | Out-Null
} catch {
    try {
        docker compose version | Out-Null
    } catch {
        Write-Host "❌ 错误: Docker Compose 未安装" -ForegroundColor Red
        Write-Host "请先安装 Docker Compose"
        exit 1
    }
}

Write-Host ""

# 检查环境变量文件
if (-not (Test-Path "backend\.env")) {
    Write-Host "📝 环境变量文件不存在，开始配置..." -ForegroundColor Yellow
    
    # 运行环境变量配置脚本
    if (Test-Path "setup_env.ps1") {
        & .\setup_env.ps1
    } else {
        Write-Host "⚠️  警告: 找不到 setup_env.ps1，请手动创建环境变量文件" -ForegroundColor Yellow
        Write-Host "参考文档: ENV_SETUP.md"
        exit 1
    }
} else {
    Write-Host "✅ 环境变量文件已存在" -ForegroundColor Green
}

Write-Host ""
Write-Host "🚀 开始构建并启动服务..." -ForegroundColor Cyan
Write-Host ""

# 停止旧容器（如果存在）
Write-Host "🧹 清理旧容器..." -ForegroundColor Yellow
try {
    docker-compose down 2>$null
} catch {
    # 忽略错误
}

# 构建并启动
Write-Host "🔨 构建镜像..." -ForegroundColor Yellow
docker-compose build

Write-Host "▶️  启动服务..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "⏳ 等待服务启动（约 30 秒）..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查服务状态
Write-Host ""
Write-Host "📊 检查服务状态..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "✅ 服务启动完成！" -ForegroundColor Green
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "📌 访问地址：" -ForegroundColor Cyan
Write-Host ""
Write-Host "  🌐 前端界面: http://localhost:3000" -ForegroundColor White
Write-Host "  📚 API 文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  ❤️  健康检查: http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🔑 默认账号：" -ForegroundColor Cyan
Write-Host ""
Write-Host "  用户名: admin" -ForegroundColor White
Write-Host "  密码: Ykxx@2025" -ForegroundColor White
Write-Host ""
Write-Host "  ⚠️  首次登录后请立即修改密码！" -ForegroundColor Yellow
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "📖 常用命令：" -ForegroundColor Cyan
Write-Host ""
Write-Host "  查看日志:   docker-compose logs -f" -ForegroundColor White
Write-Host "  重启服务:   docker-compose restart" -ForegroundColor White
Write-Host "  停止服务:   docker-compose stop" -ForegroundColor White
Write-Host "  删除服务:   docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 部署完成！祝您使用愉快！" -ForegroundColor Green
Write-Host ""

