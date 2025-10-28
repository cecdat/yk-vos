# 网关自动同步架构说明

## 概述

系统实现了网关数据的自动同步和本地数据库优先查询机制，确保前端页面能够快速获取网关状态，同时减少对VOS API的调用压力。

## 架构设计

### 1. 数据流程

```
┌─────────────────────────────────────────────────────────────┐
│                    三层存储架构                               │
└─────────────────────────────────────────────────────────────┘

前端页面查询
    ↓
Next.js API 代理 (/api/v1/vos-api/instances/{id}/GetGatewayMapping)
    ↓
Backend API 路由 (query_vos_api)
    ↓
VosCacheService.get_cached_data()
    ├─→ 检查数据库缓存 (1️⃣)
    │   ├─ 如果存在且未过期 → 返回数据库数据
    │   └─ 如果过期或不存在 → 继续
    │
    └─→ 从VOS API获取 (2️⃣)
        ├─ 调用 VOS API
        └─ 保存到数据库缓存
            └─ 返回数据
```

### 2. 双写策略

网关数据同时存储在两个地方：

#### 2.1 通用缓存表 (`vos_data_cache`)
- **用途**: API代理层缓存，提供快速查询
- **存储内容**: 完整的VOS API响应数据
- **更新频率**: 根据缓存TTL自动更新
- **查询**: 前端API请求优先查询此表

#### 2.2 专用网关表 (`gateways`)
- **用途**: 网关管理页面专用数据源
- **存储内容**: 结构化的网关信息 + 原始数据
- **更新频率**: 每分钟同步一次
- **查询**: 可用于快速查询和统计

### 3. 定时同步任务

#### 3.1 网关专用同步 (`sync_all_instances_gateways`)

**频率**: 每分钟执行一次

**任务配置**: `celery_app.py`
```python
'sync-all-gateways-every-1min': {
    'task': 'app.tasks.sync_tasks.sync_all_instances_gateways',
    'schedule': 60.0,  # 每分钟同步一次
},
```

**执行逻辑**:
1. 遍历所有启用的VOS实例
2. 调用 `VosSyncEnhanced.sync_gateways('both')`
3. 同步对接网关 (GetGatewayMapping) 和落地网关 (GetGatewayRouting)
4. 同时更新 `vos_data_cache` 和 `gateways` 表

#### 3.2 增强版全量同步 (`sync_all_instances_enhanced`)

**频率**: 每2分钟执行一次

**任务配置**: `celery_app.py`
```python
'sync-all-instances-enhanced-every-2min': {
    'task': 'app.tasks.sync_tasks.sync_all_instances_enhanced',
    'schedule': 120.0,  # 每2分钟同步一次
},
```

**同步内容**:
- 在线话机 (phones)
- 网关数据 (gateways)
- 费率组 (fee_rate_groups)
- 套餐数据 (suites)

#### 3.3 通用API缓存同步 (`sync_all_vos_common_apis`)

**频率**: 每分钟检查一次

**更新策略**:
- 根据API的重要性设置不同的同步间隔
- 配置数据 (GetGatewayMapping) 每小时同步一次
- 在线状态 (GetGatewayMappingOnline) 每30秒同步一次

### 4. 缓存机制

#### 4.1 数据库缓存 (`VosDataCache`)

**字段说明**:
- `api_path`: API路径，如 `/external/server/GetGatewayMapping`
- `cache_key`: 基于参数生成的MD5键
- `response_data`: 完整的VOS响应数据 (JSONB)
- `is_valid`: 数据是否有效
- `synced_at`: 最后同步时间
- `expires_at`: 过期时间

**TTL设置**:
```python
# 不同API的缓存过期时间
TTL_CONFIG = {
    '/external/server/GetGatewayMapping': 3600,      # 1小时
    '/external/server/GetGatewayMappingOnline': 30,  # 30秒
    '/external/server/GetGatewayRouting': 3600,      # 1小时
    '/external/server/GetGatewayRoutingOnline': 30, # 30秒
}
```

#### 4.2 查询优先级

1. **强制刷新** (`force_refresh=True`): 直接从VOS API获取
2. **数据库缓存**: 检查是否存在且未过期
3. **缓存过期**: 自动从VOS API获取并更新缓存

### 5. 前端查询流程

#### 5.1 网关页面 (`/gateway`)

```typescript
// 前端调用
const res = await api.post(
  `/vos-api/instances/${currentVOS.id}/GetGatewayMapping`, 
  {}  // 空对象表示查询全部
)

// 后端处理流程
1. query_vos_api() 接收请求
2. VosCacheService.get_cached_data() 查询缓存
3. 检查 database → 如果未过期直接返回
4. 如果过期或无数据 → 调用VOS API → 更新缓存 → 返回
5. 前端收到数据: res.data.gatewayMappings
```

#### 5.2 数据格式

**VOS原始响应**:
```json
{
  "retCode": 0,
  "gatewayMappings": [
    {
      "name": "网关A",
      "ip": "192.168.1.100",
      "port": 5060,
      // ... 其他字段
    }
  ]
}
```

**专用表字段** (`gateways`):
```json
{
  "gateway_name": "网关A",
  "gateway_type": "mapping",
  "ip_address": "192.168.1.100",
  "port": 5060,
  "is_online": true,
  "asr": 0.95,
  "acd": 180,
  "concurrent_calls": 50,
  "raw_data": {
    // VOS原始数据 + 在线状态
    "_data_sources": {
      "config": {...},
      "online": {...}
    }
  }
}
```

### 6. 优势

#### 6.1 性能优势
- **数据库查询**: 响应时间 < 10ms
- **VOS API调用**: 响应时间 > 100ms
- **减少VOS压力**: 本地缓存有效期内不调用VOS API

#### 6.2 可靠性优势
- **离线可用**: 缓存未过期时无需连接VOS
- **降级策略**: VOS故障时仍然可以查看历史数据
- **数据一致性**: 通过定时同步保持数据新鲜度

#### 6.3 实时性保障
- **在线状态**: 30秒更新一次
- **配置数据**: 1小时更新一次
- **手动刷新**: 支持强制刷新获取最新数据

### 7. 监控和调试

#### 7.1 查看同步日志

```bash
# 查看Celery任务日志
docker logs yk_vos_celery_worker -f

# 查看Celery Beat调度日志
docker logs yk_vos_celery_beat -f
```

#### 7.2 检查缓存状态

```sql
-- 查看网关缓存
SELECT 
  api_path,
  cache_key,
  synced_at,
  expires_at,
  is_valid,
  ret_code
FROM vos_data_cache
WHERE api_path IN (
  '/external/server/GetGatewayMapping',
  '/external/server/GetGatewayRouting'
)
ORDER BY synced_at DESC;

-- 查看网关专用表
SELECT 
  gateway_name,
  gateway_type,
  is_online,
  synced_at,
  updated_at
FROM gateways
ORDER BY synced_at DESC;
```

#### 7.3 手动触发同步

```python
# 在Python Shell中执行
from app.tasks.sync_tasks import sync_instance_gateways_enhanced
from app.core.db import SessionLocal

db = SessionLocal()
result = sync_instance_gateways_enhanced(instance_id=1)
print(result)
db.close()
```

### 8. 配置说明

#### 8.1 修改同步频率

编辑 `backend/app/tasks/celery_app.py`:
```python
# 修改网关同步频率为30秒
'sync-all-gateways-every-30sec': {
    'task': 'app.tasks.sync_tasks.sync_all_instances_gateways',
    'schedule': 30.0,  # 30秒
},
```

重启服务后生效：
```bash
docker-compose restart celery-beat
```

#### 8.2 修改缓存TTL

编辑 `backend/app/core/vos_cache_service.py`:
```python
# 修改缓存过期时间
TTL_CONFIG = {
    '/external/server/GetGatewayMapping': 1800,  # 30分钟
}
```

## 总结

系统通过三层存储和定时同步机制，实现了：

1. ✅ **本地数据库优先查询** - 快速响应
2. ✅ **自动同步** - 定时更新数据
3. ✅ **实时状态** - 在线状态30秒更新
4. ✅ **降级策略** - VOS故障时仍可查询历史数据
5. ✅ **减少VOS压力** - 智能缓存机制

系统已完全满足"网关数据自动同步更新，页面查询优先查询本地数据库"的需求。

