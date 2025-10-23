# VOS3000 API 接口规范

## 基本规范

### 1. 接口格式
- **格式**: JSON
- **编码**: UTF-8
- **请求方式**: POST
- **Content-Type**: `text/html;charset=UTF-8`

### 2. 返回码规范
- **成功**: `retCode = 0`
- **失败**: `retCode != 0`，错误信息在 `exception` 字段中

### 3. 错误格式示例
```json
{
  "retCode": -10007,
  "exception": "Not found, operation failed."
}
```

## VOSClient 使用说明

### 初始化客户端

```python
from app.core.vos_client import VOSClient

# 创建客户端实例
client = VOSClient(base_url="http://vos.example.com", timeout=30)
```

### 发送 API 请求

```python
# 调用 API
result = client.post('/external/server/GetAllCustomers', payload={'type': 1})

# 检查是否成功
if client.is_success(result):
    # 处理成功响应
    customers = result.get('infoCustomerBriefs', [])
    print(f"获取到 {len(customers)} 个客户")
else:
    # 处理错误
    error_msg = client.get_error_message(result)
    print(f"API 调用失败: {error_msg}")
```

### 错误码定义

VOSClient 自定义错误码：

| 错误码 | 说明 |
|--------|------|
| -1 | HTTP 错误（4xx, 5xx） |
| -2 | 请求超时 |
| -3 | 网络错误 |
| -4 | JSON 解析错误 |
| -99 | 未知错误 |
| -999 | 返回数据中缺少 retCode 字段 |

VOS3000 服务器错误码（部分）：

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| -10007 | 资源未找到 |
| 其他 | 参考 VOS3000 官方文档 |

## 常用 API 接口

### 1. 获取所有客户
**接口**: `/external/server/GetAllCustomers`

**请求参数**:
```json
{
  "type": 1
}
```

**成功响应**:
```json
{
  "retCode": 0,
  "infoCustomerBriefs": [
    {
      "account": "客户账号",
      "money": 0.0,
      "limitMoney": 1000.0
    }
  ]
}
```

### 2. 获取在线话机
**接口**: `/external/server/GetPhoneOnline`

**请求参数**:
```json
{}
```

**成功响应**:
```json
{
  "retCode": 0,
  "infoPhoneOnlines": [
    {
      "e164": "13800138000",
      "status": "online"
    }
  ]
}
```

## 最佳实践

### 1. 错误处理
```python
result = client.post('/api/endpoint', payload={})

if not client.is_success(result):
    logger.error(f"VOS API 调用失败: {client.get_error_message(result)}")
    return {
        'error': True,
        'message': result.get('exception', 'Unknown error')
    }
```

### 2. 日志记录
```python
import logging

logger = logging.getLogger(__name__)

# VOSClient 会自动记录详细日志
# DEBUG 级别: 请求/响应详情
# WARNING 级别: VOS 返回的业务错误
# ERROR 级别: 网络/系统错误
```

### 3. 超时设置
```python
# 根据实际网络情况调整超时时间
client = VOSClient(base_url="http://vos.example.com", timeout=60)
```

### 4. 资源清理
```python
# VOSClient 会在对象销毁时自动关闭连接
# 但在长期运行的应用中，建议复用客户端实例
```

## 注意事项

1. **编码问题**: 所有 JSON 数据使用 UTF-8 编码，支持中文字符
2. **返回码检查**: 始终检查 `retCode` 字段，不要只依赖 HTTP 状态码
3. **异常处理**: VOSClient 会捕获所有异常并返回统一格式的错误响应
4. **并发请求**: 每个 VOSClient 实例使用独立的 HTTP 客户端，支持并发
5. **日志级别**: 生产环境建议使用 INFO 或 WARNING 级别，避免过多 DEBUG 日志

## 示例代码

### 完整示例：获取并处理客户数据

```python
from app.core.vos_client import VOSClient
import logging

logger = logging.getLogger(__name__)

def get_customers(vos_url: str) -> dict:
    """获取 VOS 客户列表"""
    client = VOSClient(vos_url)
    
    # 调用 API
    result = client.post('/external/server/GetAllCustomers', {'type': 1})
    
    # 检查结果
    if not client.is_success(result):
        logger.error(f"获取客户失败: {client.get_error_message(result)}")
        return {
            'success': False,
            'error': result.get('exception', 'Unknown error'),
            'customers': []
        }
    
    # 处理成功响应
    customers = result.get('infoCustomerBriefs', [])
    logger.info(f"成功获取 {len(customers)} 个客户")
    
    return {
        'success': True,
        'customers': customers,
        'count': len(customers)
    }
```

## 更新日志

### v1.1 (2025-10-21)
- 增强错误处理机制
- 添加详细的日志记录
- 增加 `is_success()` 和 `get_error_message()` 辅助方法
- 明确 UTF-8 编码处理
- 完善错误码定义

### v1.0 (初始版本)
- 基本 POST 请求功能
- 简单错误处理

