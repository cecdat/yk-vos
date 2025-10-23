# 前端 API 连接问题修复指南

## 📋 问题描述

1. **登录失败 - Network Error**
   - 前端无法连接到后端 API
   - 浏览器报错：`AxiosError: Network Error`

2. **登录页不必要的 API 调用**
   - 在登录页面就调用 `api/v1/vos/instances` 接口
   - 导致额外的错误日志

## ✅ 已修复内容

### 1. 环境变量配置
- 修正环境变量名：`NEXT_PUBLIC_API_URL` → `NEXT_PUBLIC_API_BASE`
- 修正值格式：添加 `/api/v1` 后缀

### 2. VOSContext 优化
- 仅在用户已登录时才获取 VOS 列表
- 登录页面不再产生不必要的 API 请求

### 3. 自动化配置
- `init-deploy.sh` 自动检测和配置服务器 IP
- `setup-frontend-env.sh` 提供手动配置选项

---

## 🚀 在服务器上应用修复

### 方法 1：自动配置（推荐）

#### 步骤 1：拉取最新代码
```bash
cd /data/yk-vos
git pull
```

#### 步骤 2：重新配置并重启
```bash
# 运行配置脚本（会自动检测 IP）
chmod +x setup-frontend-env.sh
./setup-frontend-env.sh
```

脚本会：
1. 提示输入服务器地址
2. 自动更新 `docker-compose.yaml`
3. 重启前端容器

---

### 方法 2：手动配置

#### 步骤 1：拉取代码
```bash
cd /data/yk-vos
git pull
```

#### 步骤 2：手动编辑 docker-compose.yaml

找到前端服务的环境变量配置（约第 82 行）：

```yaml
  frontend:
    ...
    environment:
      NEXT_PUBLIC_API_BASE: ${NEXT_PUBLIC_API_BASE:-http://localhost:8000/api/v1}
```

将 `localhost` 改为你的**服务器 IP 地址或域名**：

```yaml
  frontend:
    ...
    environment:
      NEXT_PUBLIC_API_BASE: http://YOUR_SERVER_IP:8000/api/v1
```

**示例**：
- 如果服务器 IP 是 `192.168.2.101`：
  ```yaml
  NEXT_PUBLIC_API_BASE: http://192.168.2.101:8000/api/v1
  ```

- 如果使用域名：
  ```yaml
  NEXT_PUBLIC_API_BASE: https://api.yourdomain.com/api/v1
  ```

#### 步骤 3：重启前端容器

```bash
docker-compose restart frontend
```

---

### 方法 3：重新部署

如果以上方法不行，完全重新构建和部署：

```bash
cd /data/yk-vos
git pull

# 停止所有服务
docker-compose down

# 重新构建基础镜像
docker-compose -f docker-compose.base.yaml build --no-cache

# 启动服务
docker-compose up -d
```

---

## ✅ 验证修复

### 1. 检查前端环境变量

```bash
docker-compose exec frontend env | grep NEXT_PUBLIC_API_BASE
```

**预期输出**：
```
NEXT_PUBLIC_API_BASE=http://YOUR_SERVER_IP:8000/api/v1
```

### 2. 检查浏览器控制台

1. 打开浏览器，访问 `http://YOUR_SERVER_IP:3000`
2. 打开开发者工具（F12）
3. 查看 Network 选项卡
4. 尝试登录

**预期行为**：
- ✅ 看到请求发送到 `http://YOUR_SERVER_IP:8000/api/v1/auth/login`
- ✅ 登录页面不会看到 `/vos/instances` 请求
- ✅ 登录成功后才会看到 `/vos/instances` 请求

### 3. 测试登录

使用默认账户登录：
- **用户名**: `admin`
- **密码**: `admin123`

**预期结果**：
- ✅ 登录成功，跳转到仪表盘
- ✅ 可以看到 VOS 实例列表

---

## 🔧 常见问题

### Q1: 修改后仍然无法登录

**检查清单**：
1. 确认服务器 IP 地址正确
2. 确认后端服务正在运行：`docker-compose ps backend`
3. 确认端口 8000 可以访问：`curl http://YOUR_SERVER_IP:8000/health`
4. 检查防火墙设置

### Q2: 浏览器仍然请求 localhost

**原因**：浏览器缓存了旧的配置

**解决方案**：
1. 清除浏览器缓存
2. 使用无痕模式
3. 强制刷新页面（Ctrl+F5）

### Q3: CORS 错误

**症状**：浏览器控制台显示 CORS 错误

**解决方案**：
检查后端配置，确保允许前端域名：
```bash
docker-compose logs backend | grep CORS
```

---

## 📊 配置检查清单

- [ ] 已拉取最新代码
- [ ] 已更新 `docker-compose.yaml` 中的 API 地址
- [ ] 已重启前端容器
- [ ] 前端环境变量正确
- [ ] 后端服务正在运行
- [ ] 可以访问后端 API（`/health` 端点）
- [ ] 登录功能正常
- [ ] 登录页不再调用 VOS 接口

---

## 💡 最佳实践

### 生产环境建议

1. **使用域名而不是 IP**：
   ```yaml
   NEXT_PUBLIC_API_BASE: https://api.yourdomain.com/api/v1
   ```

2. **启用 HTTPS**：
   - 使用 Nginx 作为反向代理
   - 配置 SSL 证书（Let's Encrypt）

3. **配置环境变量文件**：
   创建 `.env` 文件：
   ```bash
   NEXT_PUBLIC_API_BASE=http://YOUR_SERVER_IP:8000/api/v1
   ```

4. **使用 Docker Compose 覆盖**：
   创建 `docker-compose.override.yaml`：
   ```yaml
   services:
     frontend:
       environment:
         NEXT_PUBLIC_API_BASE: http://YOUR_SERVER_IP:8000/api/v1
   ```

---

## 🎯 总结

这次修复解决了：
1. ✅ 前端无法连接后端的问题
2. ✅ 登录页不必要的 API 调用
3. ✅ 提供了自动化配置工具
4. ✅ 简化了部署流程

现在系统应该可以正常登录和使用了！🎉

