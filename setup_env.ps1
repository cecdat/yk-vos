# YK-VOS 环境变量快速配置脚本 (PowerShell)

Write-Host "🚀 开始配置 YK-VOS 环境变量..." -ForegroundColor Green

# 生成随机密钥（Windows）
$bytes = New-Object byte[] 32
([System.Security.Cryptography.RNGCryptoServiceProvider]::Create()).GetBytes($bytes)
$SECRET_KEY = [System.BitConverter]::ToString($bytes).Replace('-', '').ToLower()

# 后端环境变量
$backendEnv = @"
# Database Configuration
DATABASE_URL=postgresql://vos:vos123@db:5432/vosdb

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# JWT Secret Key
SECRET_KEY=$SECRET_KEY

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=YK-VOS API

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
"@

$backendEnv | Out-File -FilePath "backend\.env" -Encoding utf8 -NoNewline
Write-Host "✅ 后端环境变量已创建: backend\.env" -ForegroundColor Green

# 前端环境变量
$frontendEnv = @"
# API Base URL
# 本地开发使用 http://localhost:8000/api/v1
# Docker 环境使用 http://backend:8000/api/v1
# 生产环境修改为实际服务器地址
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
"@

$frontendEnv | Out-File -FilePath "frontend\.env" -Encoding utf8 -NoNewline
Write-Host "✅ 前端环境变量已创建: frontend\.env" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 环境变量配置完成！" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 重要提示：" -ForegroundColor Yellow
Write-Host "   - 已生成随机 SECRET_KEY"
Write-Host "   - 前端默认使用 http://localhost:8000/api/v1"
Write-Host "   - 如需修改，请编辑 frontend\.env"
Write-Host ""
Write-Host "▶️  下一步: 运行 docker-compose up --build -d" -ForegroundColor Green
Write-Host ""

