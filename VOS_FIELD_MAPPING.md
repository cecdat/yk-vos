# VOS话单字段映射说明

## 📋 VOS API实际返回数据结构

### 响应格式

```json
[
  {
    "retCode": 0,
    "infoCdrs": [
      {
        // 话单数据...
      }
    ]
  }
]
```

**说明**:
- VOS API返回的是**数组**格式（注意不是对象）
- 数组第一个元素包含 `retCode` 和 `infoCdrs`
- `retCode`: 0=成功，非0=失败
- `infoCdrs`: 话单数据数组

---

## 🔄 字段完整映射表

### 基础信息

| VOS字段 | 数据库字段 | 类型 | 说明 | 示例 |
|---------|-----------|------|------|------|
| `flowNo` | `flow_no` | VARCHAR(64) | 话单唯一标识 ⭐ 去重键 | "330455246" |
| `account` | `account` | VARCHAR(64) | 账户号码 | "百融消金" |
| `accountName` | `account_name` | VARCHAR(128) | 账户名称 | "百融" |

### 主叫信息

| VOS字段 | 数据库字段 | 类型 | 说明 | 示例 |
|---------|-----------|------|------|------|
| `callerE164` | `caller_e164` | VARCHAR(64) | 主叫号码 | "202509241816" |
| `callerAccessE164` | - | - | 主叫接入号 | "202509241816" |
| `callerProductId` | - | - | 主叫产品ID | "FreeSWITCH-mod_sofia..." |
| `callerToGatewayE164` | - | - | 主叫到网关号码 | "90713102" |
| `callerGateway` | - | - | 主叫网关 | "百融消金58信用贷" |
| `callerip` | - | - | 主叫IP | "120.133.80.139" |

### 被叫信息

| VOS字段 | 数据库字段 | 类型 | 说明 | 示例 |
|---------|-----------|------|------|------|
| `calleeE164` | - | - | 被叫原始号码 | "22217342625719" |
| `calleeAccessE164` | `callee_access_e164` | VARCHAR(64) | 被叫接入号 ⭐ | "17342625719" |
| `calleeProductId` | - | - | 被叫产品ID | "" |
| `calleeToGatewayE164` | - | - | 被叫到网关号码 | "17342625719" |
| `calleeGateway` | `callee_gateway` | VARCHAR(64) | 被叫网关 | "深圳腾龙消金AI" |
| `calleeip` | `callee_ip` | VARCHAR(64) | 被叫IP | "113.219.238.5" |

### 时间信息

| VOS字段 | 数据库字段 | 类型 | 说明 | 示例 | 转换 |
|---------|-----------|------|------|------|------|
| `start` | `start` | TIMESTAMP | 起始时间 ⭐ 分区键 | 1760922383500 | 毫秒→datetime |
| `stop` | `stop` | TIMESTAMP | 终止时间 | 1760922383500 | 毫秒→datetime |

**时间戳转换**:
```python
# VOS返回毫秒时间戳
start_timestamp = 1760922383500

# 转换为datetime
from datetime import datetime
start_dt = datetime.fromtimestamp(start_timestamp / 1000.0)
# 结果: 2025-10-20 09:06:23
```

### 时长和费用

| VOS字段 | 数据库字段 | 类型 | 说明 | 示例 |
|---------|-----------|------|------|------|
| `holdTime` | `hold_time` | INTEGER | 通话时长(秒) | 0 |
| `feeTime` | `fee_time` | INTEGER | 计费时长(秒) | 0 |
| `fee` | `fee` | NUMERIC(10,4) | 通话费用 | 0 |
| `feePrefix` | - | - | 费用前缀 | "2" |
| `suiteFee` | - | - | 套餐费用 | 0 |
| `suiteFeeTime` | - | - | 套餐计费时长 | 0 |

### 代理商信息

| VOS字段 | 数据库字段 | 类型 | 说明 | 示例 |
|---------|-----------|------|------|------|
| `agentAccount` | - | - | 代理商账户 | "深圳腾龙消金AI" |
| `agentName` | - | - | 代理商名称 | "" |
| `agentFee` | - | - | 代理商费用 | 0 |
| `agentFeeTime` | - | - | 代理商计费时长 | 0 |
| `agentFeePrefix` | - | - | 代理商费用前缀 | "2" |
| `agentSuiteFee` | - | - | 代理商套餐费用 | 0 |
| `agentSuiteFeeTime` | - | - | 代理商套餐时长 | 0 |

### 呼叫状态

| VOS字段 | 数据库字段 | 类型 | 说明 | 可能值 |
|---------|-----------|------|------|--------|
| `endDirection` | `end_direction` | SMALLINT | 挂断方 | 0=主叫, 1=被叫, 2=服务器 |
| `endReason` | `end_reason` | VARCHAR(128) | 终止原因 | 503, -69, 200等 |
| `callLevel` | - | - | 呼叫等级 | 4 |

### 计费信息

| VOS字段 | 数据库字段 | 类型 | 说明 | 可能值 |
|---------|-----------|------|------|--------|
| `billingType` | - | - | 计费类型 | 0 |
| `billingMode` | - | - | 计费模式 | 1 |

### 原始数据

| VOS字段 | 数据库字段 | 类型 | 说明 |
|---------|-----------|------|------|
| *全部字段* | `raw` | JSONB | 完整原始JSON数据 ⭐ |

---

## 🎯 关键字段说明

### 1. flowNo（话单唯一标识）⭐⭐⭐⭐⭐

- **VOS类型**: INTEGER
- **存储类型**: VARCHAR(64)
- **用途**: 去重键（UNIQUE索引）
- **示例**: VOS返回 `330455246`，存储为 `"330455246"`

```python
flow_no = c.get('flowNo')  # 330455246
flow_no_str = str(flow_no)  # "330455246"
```

### 2. start/stop（时间戳）⭐⭐⭐⭐⭐

- **VOS格式**: 毫秒时间戳（13位数字）
- **存储格式**: TIMESTAMP
- **用途**: start是TimescaleDB分区键

**转换示例**:
```python
# VOS返回
{
  "start": 1760922383500,  # 毫秒
  "stop": 1760922383500
}

# 转换
start_dt = datetime.fromtimestamp(1760922383500 / 1000.0)
# 结果: 2025-10-20 09:06:23.500000

# 存储到数据库
INSERT INTO cdrs (start, stop, ...) VALUES 
  ('2025-10-20 09:06:23.500', '2025-10-20 09:06:23.500', ...)
```

### 3. endReason（终止原因）⭐⭐⭐

- **VOS类型**: INTEGER（可能为负数）
- **存储类型**: VARCHAR(128)
- **原因**: 需要支持负数（如-69）和字符串

**示例**:
```python
# VOS返回
{
  "endReason": 503    # HTTP状态码类似
}
{
  "endReason": -69    # 负数错误码
}

# 转换
end_reason = str(c.get('endReason'))  # "503" 或 "-69"
```

### 4. raw（原始数据）⭐⭐⭐⭐

- **类型**: JSONB（PostgreSQL/TimescaleDB）
- **用途**: 保存完整VOS返回数据，支持未来扩展

**优势**:
- ✅ 自动压缩（节省空间）
- ✅ 支持JSON查询（如 `raw->>'callerGateway'`）
- ✅ 支持GIN索引（加速JSON查询）
- ✅ 保留所有原始信息

---

## 📊 实际数据示例

### 示例1：正常话单

```json
{
  "flowNo": 330455246,
  "account": "百融消金",
  "accountName": "百融",
  "callerE164": "202509241816",
  "calleeAccessE164": "17342625719",
  "calleeGateway": "深圳腾龙消金AI",
  "calleeip": "113.219.238.5",
  "start": 1760922383500,
  "stop": 1760922383500,
  "holdTime": 0,
  "feeTime": 0,
  "fee": 0,
  "endDirection": 1,
  "endReason": 503
}
```

**存储后**:
```sql
flow_no: "330455246"
account: "百融消金"
account_name: "百融"
caller_e164: "202509241816"
callee_access_e164: "17342625719"
callee_gateway: "深圳腾龙消金AI"
callee_ip: "113.219.238.5"
start: 2025-10-20 09:06:23.500000
stop: 2025-10-20 09:06:23.500000
hold_time: 0
fee_time: 0
fee: 0.0000
end_direction: 1
end_reason: "503"
```

### 示例2：失败话单（网关为空）

```json
{
  "flowNo": 330455275,
  "calleeGateway": "",
  "calleeip": "",
  "endDirection": 2,
  "endReason": -69
}
```

**存储后**:
```sql
callee_gateway: ""
callee_ip: ""
end_direction: 2
end_reason: "-69"  -- 注意负数也转为字符串
```

---

## 🔍 字段查询示例

### 1. 通过flowNo查询

```sql
SELECT * FROM cdrs WHERE flow_no = '330455246';
```

### 2. 通过时间范围查询（利用TimescaleDB分区）

```sql
SELECT * FROM cdrs 
WHERE start >= '2025-10-20 00:00:00' 
  AND start < '2025-10-21 00:00:00';
```

### 3. 查询特定账户话单

```sql
SELECT * FROM cdrs 
WHERE account = '百融消金' 
  AND start >= NOW() - INTERVAL '7 days'
ORDER BY start DESC;
```

### 4. 查询JSONB原始数据

```sql
-- 查询原始callerGateway
SELECT 
    flow_no,
    raw->>'callerGateway' as caller_gateway_from_raw,
    raw->>'agentAccount' as agent_account
FROM cdrs 
WHERE flow_no = '330455246';
```

### 5. 统计各网关话单量

```sql
SELECT 
    callee_gateway,
    COUNT(*) as call_count,
    SUM(fee) as total_fee
FROM cdrs
WHERE start >= NOW() - INTERVAL '1 day'
GROUP BY callee_gateway
ORDER BY call_count DESC;
```

---

## ⚠️ 注意事项

### 1. VOS返回数组格式

VOS API返回的是**数组**，需要特殊处理：

```python
# ❌ 错误
result = client.call_api(...)
cdrs = result.get('infoCdrs')  # 会失败，因为result是数组

# ✅ 正确
result = client.call_api(...)
if isinstance(result, list) and len(result) > 0:
    result = result[0]  # 取第一个元素
cdrs = result.get('infoCdrs')
```

### 2. 时间戳单位

VOS返回的是**毫秒**时间戳，不是秒：

```python
# ❌ 错误（会得到1970年的时间）
start_dt = datetime.fromtimestamp(1760922383500)

# ✅ 正确（除以1000转为秒）
start_dt = datetime.fromtimestamp(1760922383500 / 1000.0)
```

### 3. flowNo类型转换

VOS返回INTEGER，数据库存储VARCHAR：

```python
# ❌ 错误（类型不匹配）
flow_no = c.get('flowNo')  # 330455246 (int)
INSERT INTO cdrs (flow_no) VALUES (330455246)  # 可能报错

# ✅ 正确
flow_no_str = str(c.get('flowNo'))  # "330455246" (str)
```

### 4. 空值处理

某些字段可能为空字符串：

```python
# VOS返回
{
  "calleeGateway": "",
  "calleeip": ""
}

# 存储为空字符串，不是NULL
callee_gateway = c.get('calleeGateway', '')  # ""
```

---

## 📚 相关文档

- **TimescaleDB部署**: `TIMESCALEDB_DEPLOYMENT.md`
- **快速参考**: `QUICK_REFERENCE_CDR.md`
- **优化方案**: `CDR_OPTIMIZATION_PLAN.md`
- **版本说明**: `V2_RELEASE_NOTES.md`

---

**最后更新**: 2025-10-23
**版本**: v2.0
**基于**: 实际VOS API返回数据

