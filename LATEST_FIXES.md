# 最新修复说明

## 修复时间
2025-10-23

## 修复内容

### 1. ✅ 删除左侧导航中的"VOS 节点"菜单
**问题**：左侧导航中有重复的"VOS 节点"入口，系统设置中已经有VOS节点管理。

**解决方案**：
- 修改 `frontend/app/layout.tsx`，删除了左侧导航中的"VOS 节点"菜单项
- 用户现在可以通过"系统设置"访问VOS节点管理

### 2. ✅ 修复VOS节点删除失败
**问题**：删除VOS节点时提示"删除失败"，因为存在外键关联的数据。

**解决方案**：
- 修改 `backend/app/routers/vos.py` 的 `delete_instance` 接口
- 实现了级联删除逻辑，按顺序删除：
  1. 客户数据 (`customers`)
  2. 话机数据 (`phones`)
  3. 缓存数据 (`vos_data_cache`)
  4. 话单数据 (`cdrs`)
  5. VOS实例本身
- 添加了详细的删除日志和错误处理
- 返回删除的详细统计信息

**使用示例**：
删除VOS节点时，系统会自动清理所有关联数据，并返回删除统计：
```json
{
  "message": "VOS 实例删除成功",
  "deleted": {
    "instance_name": "demo-vos",
    "customers": 150,
    "phones": 200,
    "cache_entries": 500,
    "cdrs": 10000
  }
}
```

### 3. ✅ 修复缓存管理页面500错误
**问题**：访问缓存管理页面时后端报错 `'Session' object has no attribute 'func'`

**解决方案**：
- 修改 `backend/app/core/vos_cache_service.py`
- 在文件顶部添加 `from sqlalchemy import and_, func` 导入
- 修改 `get_cache_stats` 方法中的 `self.db.func.count` 为 `func.count`

### 4. ✅ 添加会话超时自动退出功能
**问题**：会话超时后，页面没有自动跳转到登录页，导致数据一直处于加载中状态。

**解决方案**：
- 修改 `frontend/lib/api.ts`，添加响应拦截器
- 当检测到 401 或 403 错误时：
  1. 自动清除 localStorage 中的 token
  2. 跳转到登录页，并添加 `?timeout=1` 参数
- 修改 `frontend/app/login/page.tsx`：
  1. 使用 `useEffect` 检测 URL 参数
  2. 如果检测到 `timeout=1`，显示"会话已超时，请重新登录"提示
  3. 超时提示使用黄色背景，与成功/失败提示区分

**用户体验**：
- 会话超时后自动跳转到登录页
- 显示友好的黄色提示信息："会话已超时，请重新登录"
- 无需用户手动刷新页面

### 5. ✅ 修改平台名称
**问题**：平台名称需要更改为"云客信息-VOS管理平台"

**解决方案**：
- 修改 `frontend/app/login/page.tsx`：登录页面标题
- 修改 `frontend/app/layout.tsx`：侧边栏Logo名称

**修改位置**：
- 登录页：`云客信息-VOS管理平台`
- 侧边栏：`云客信息-VOS管理平台`

## 部署步骤

### 方式一：在服务器上拉取最新代码（推荐）

```bash
# 1. 进入项目目录
cd /data/yk-vos

# 2. 拉取最新代码
git pull

# 3. 重新构建并重启前端和后端服务
docker-compose up -d --build backend frontend

# 4. 查看日志确认启动成功
docker-compose logs -f backend frontend
```

### 方式二：使用快速更新脚本

```bash
cd /data/yk-vos
./quick-update.sh
```

## 验证步骤

### 1. 验证导航菜单
- 登录系统后，检查左侧导航是否已移除"VOS 节点"菜单
- 确认"系统设置"中可以正常访问VOS节点管理

### 2. 验证VOS节点删除
- 前往"系统设置" → "VOS节点管理"
- 尝试删除一个测试节点
- 确认删除成功，并显示删除统计信息

### 3. 验证缓存管理
- 访问"缓存管理"页面
- 确认页面正常加载，显示缓存统计信息
- 无500错误

### 4. 验证会话超时
- 登录系统
- 等待会话超时（或手动删除浏览器 localStorage 中的 token）
- 刷新页面或进行API操作
- 确认自动跳转到登录页，并显示"会话已超时，请重新登录"

### 5. 验证平台名称
- 检查登录页标题是否为"云客信息-VOS管理平台"
- 登录后检查侧边栏Logo名称是否为"云客信息-VOS管理平台"

## 注意事项

1. **VOS节点删除**：删除操作会清理所有关联数据，包括大量话单记录，可能需要较长时间，请耐心等待。

2. **会话超时**：默认的JWT token有效期由后端配置决定，建议在生产环境中设置合理的过期时间。

3. **前端缓存**：如果修改后前端没有生效，可能是浏览器缓存问题：
   - 强制刷新：`Ctrl+F5` 或 `Cmd+Shift+R`
   - 清除浏览器缓存
   - 使用无痕模式测试

## 相关文件

### 后端
- `backend/app/routers/vos.py` - VOS节点删除逻辑
- `backend/app/core/vos_cache_service.py` - 缓存统计修复

### 前端
- `frontend/app/layout.tsx` - 导航菜单、平台名称
- `frontend/app/login/page.tsx` - 登录页标题、超时提示
- `frontend/lib/api.ts` - API拦截器、会话超时处理

## 技术要点

### 级联删除实现
```python
# 按顺序删除外键关联数据
customer_count = db.query(Customer).filter(Customer.vos_instance_id == instance_id).delete()
phone_count = db.query(Phone).filter(Phone.vos_id == instance_id).delete()
cache_count = db.query(VosDataCache).filter(VosDataCache.vos_instance_id == instance_id).delete()
cdr_count = db.query(CDR).filter(CDR.vos_id == instance_id).delete()

# 最后删除实例
db.delete(instance)
db.commit()
```

### 响应拦截器实现
```typescript
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      localStorage.removeItem('token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login?timeout=1';
      }
    }
    return Promise.reject(error);
  }
);
```

## 问题排查

如果遇到问题，请检查：

1. **Docker日志**：
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f frontend
   ```

2. **浏览器控制台**：
   - 按 F12 打开开发者工具
   - 查看 Console 和 Network 选项卡
   - 检查是否有JavaScript错误或API调用失败

3. **数据库连接**：
   ```bash
   docker-compose exec postgres psql -U vos_user -d vosadmin -c "\dt"
   ```

---

如有问题，请参考 `README.md` 和 `UPGRADE_GUIDE.md`。

