# 部署指南 - 支持内外网访问

## 部署架构

### 端口映射配置

系统通过路由器端口映射实现内外网访问：

- **前端端口映射**: `3000 → 公网` (或自定义端口)
- **后端端口映射**: `3001 → 公网` (或自定义端口)

### 工作原理

1. **前端 (Next.js)**: 
   - 监听端口: `3000`（容器内）/ `3000`（宿主机）
   - 通过 Next.js 的 `rewrites` 功能将 `/api/*` 请求代理到后端
   - 客户端访问前端时，所有 API 请求都使用相对路径 `/api/v1/*`

2. **后端 (FastAPI)**:
   - 监听端口: `3001`（容器内）/ `3001`（宿主机）
   - 前端通过 Docker 内部网络 `http://backend:3001/api/v1` 调用

3. **数据流转**:
   ```
   客户端 → 前端 (3000) → Next.js代理 → 后端 (3001) → 数据库
   ```

### 关键配置

#### 1. 前端配置 (`frontend/lib/api.ts`)

```typescript
const getBaseURL = () => {
  // 优先使用环境变量
  if (process.env.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE;
  }
  
  // 默认使用相对路径（通过Next.js代理）
  return '/api/v1';
};
```

#### 2. Next.js 代理配置 (`frontend/next.config.js`)

```javascript
async rewrites() {
  const apiUrl = process.env.BACKEND_API_URL || 'http://backend:3001';
  
  return [
    {
      source: '/api/:path*',
      destination: `${apiUrl}/api/:path*`,
    },
  ];
}
```

## 部署步骤

### 1. 环境准备

确保服务器已安装 Docker 和 Docker Compose。

### 2. 拉取代码

```bash
git clone <repository-url>
cd yk-vos
```

### 3. 配置端口映射（路由器）

在路由器管理界面设置：

- **外网端口**: `3000` → **内网IP:3000** (前端)
- **外网端口**: `3001` → **内网IP:3001** (后端，可选，用于API测试)

### 4. 环境变量配置（可选）

如果需要自定义配置，创建 `.env` 文件：

```bash
# .env
POSTGRES_USER=vosadmin
POSTGRES_PASSWORD=YourPassword
CLICKHOUSE_USER=vosadmin
CLICKHOUSE_PASSWORD=YourPassword
SECRET_KEY=YourSecretKey
```

### 5. 构建和启动

```bash
# 使用基础镜像构建脚本
docker-compose -f docker-compose.base.yaml build

# 启动服务
docker-compose up -d
```

### 6. 检查服务状态

```bash
docker-compose ps
docker-compose logs -f
```

## 访问方式

### 内网访问

- **前端**: `http://192.168.2.101:3000`
- **后端API**: `http://192.168.2.101:3001/api/v1`
- **默认账号**: `admin` / `admin123` (修改前)

### 外网访问

- **前端**: `http://your-domain.com:3000` 或 `http://your-ip:3000`
- **后端API**: `http://your-domain.com:3001/api/v1` (如果需要)
- 前端会自动将 API 请求代理到后端，无需直接访问后端端口

## 优势

### 1. 统一入口

- 客户端只需访问前端地址，API 自动通过 Next.js 代理转发
- 减少暴露端口数量

### 2. 内外网一致性

- 内网访问：`http://192.168.2.101:3000`
- 外网访问：`http://public-ip:3000`
- 两套环境的 API 调用行为一致，都使用相对路径

### 3. 易于维护

- 修改前端 API 地址只需更新 Docker Compose 环境变量
- 无需修改代码即可切换环境

## 常见问题

### Q1: 前端无法连接到后端？

**检查项**:
1. 确认后端服务已启动：`docker-compose ps`
2. 查看后端日志：`docker-compose logs backend`
3. 检查网络连通性：`docker exec -it yk_vos_frontend ping backend`

### Q2: 外网访问时前端显示但不能登录？

**可能原因**:
1. 后端未正确映射到公网
2. 检查前端浏览器控制台的错误信息
3. 查看网络请求是否正确使用相对路径 `/api/v1`

### Q3: 如何修改端口？

**方法1**: 修改 `docker-compose.yaml`
```yaml
frontend:
  ports:
    - "新端口:3000"

backend:
  ports:
    - "新端口:3001"
```

**方法2**: 使用环境变量
```bash
export FRONTEND_PORT=新端口
export BACKEND_PORT=新端口
docker-compose up -d
```

### Q4: 生产环境如何部署？

1. **使用 HTTPS**: 配置 Nginx 反向代理
2. **域名绑定**: 配置域名解析
3. **防火墙**: 只开放必要端口（80, 443）
4. **监控**: 配置日志收集和监控

示例 Nginx 配置：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 技术栈

- **前端**: Next.js 14 + React 18
- **后端**: FastAPI + Python 3
- **数据库**: PostgreSQL + ClickHouse
- **任务队列**: Celery + Redis
- **部署**: Docker + Docker Compose

## 更新日志

- **2025-01-XX**: 优化 API 配置，支持内外网访问
- **2025-01-XX**: 修改后端端口从 8000 到 3001
- **2025-01-XX**: 删除登录页面默认账号提示

## 支持

如有问题，请提交 Issue 或联系技术支持。

