# 前端API代理配置说明

## 🎯 架构说明

### 问题背景

Next.js 应用有两个运行环境：
1. **服务端**（Next.js Server）- 运行在 Docker 容器中
2. **浏览器端**（Browser）- 运行在用户的电脑上

`NEXT_PUBLIC_` 前缀的环境变量会被打包到浏览器端代码中，在用户浏览器执行，**无法访问 Docker 内部网络**。

### 解决方案：Next.js 代理

通过 Next.js 的 `rewrites` 功能，将浏览器请求代理到后端：

```
浏览器 → 前端容器(/api) → 后端容器(http://backend:8000)
```

## 🔧 配置说明

### 1. docker-compose.yaml

```yaml
frontend:
  environment:
    # 浏览器端使用相对路径
    NEXT_PUBLIC_API_BASE: /api/v1
    # Next.js 服务端代理到后端（容器网络）
    BACKEND_API_URL: http://backend:8000
```

### 2. next.config.js

```javascript
async rewrites() {
  const apiUrl = process.env.BACKEND_API_URL || 'http://backend:8000';
  return [
    {
      source: '/api/:path*',
      destination: `${apiUrl}/:path*`,
    },
  ];
}
```

## 📊 请求流程

### 之前（错误）
```
浏览器 --X--> http://localhost:8000/api/v1/auth/login
       (无法连接，localhost是用户电脑)
```

### 现在（正确）
```
浏览器 --> http://192.168.2.101:3000/api/v1/auth/login
       ↓
Next.js --> http://backend:8000/api/v1/auth/login
       (容器内部网络)
       ↓
后端API响应
```

## 🚀 部署步骤

### 服务器端操作

```bash
cd /data/yk-vos

# 1. 拉取最新代码
git pull

# 2. 重启前端服务
docker-compose restart frontend

# 3. 查看日志确认启动
docker-compose logs -f frontend
```

### 验证

1. 访问 http://服务器IP:3000/login
2. 尝试登录
3. 检查浏览器Network面板，请求应该到：
   - `http://服务器IP:3000/api/v1/auth/login` ✅
   - 而不是 `http://localhost:8000/api/v1/auth/login` ❌

## 💡 优势

1. ✅ **利用 Docker 内部网络**：前端和后端通过容器名通信
2. ✅ **避免 CORS 问题**：同源请求，无需复杂的CORS配置
3. ✅ **更好的安全性**：后端不需要暴露到公网
4. ✅ **简化配置**：无需配置服务器IP

## 🔍 调试

### 查看环境变量

```bash
# 浏览器端（打开浏览器控制台）
console.log(process.env.NEXT_PUBLIC_API_BASE)  // 应该是 /api/v1

# 服务端（在容器中）
docker-compose exec frontend env | grep API
```

### 查看代理是否工作

```bash
# 从容器内测试后端连接
docker-compose exec frontend curl http://backend:8000/health
```

## 📚 参考

- [Next.js Rewrites](https://nextjs.org/docs/api-reference/next.config.js/rewrites)
- [Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)

