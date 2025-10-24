# ClickHouse 实施指南

## 📁 需要创建/修改的文件清单

### 1. ClickHouse 初始化脚本
**文件**：`clickhouse/init/01_create_tables.sql`

### 2. ClickHouse 数据库连接
**文件**：`backend/app/core/clickhouse_db.py`

### 3. ClickHouse CDR 模型
**文件**：`backend/app/models/clickhouse_cdr.py`

### 4. 更新依赖
**文件**：`backend/requirements.txt`
添加：`clickhouse-driver>=0.2.6`

### 5. 更新配置
**文件**：`backend/app/core/config.py`

### 6. 更新 CDR 路由
**文件**：`backend/app/routers/cdr.py`

### 7. 更新启动脚本
**文件**：`backend/docker-entrypoint-clickhouse.sh`

## 🔄 迁移步骤

### 阶段 1：准备环境（30分钟）

```bash
cd /data/yk-vos

# 1. 创建 ClickHouse 目录结构
mkdir -p clickhouse/init
mkdir -p data/clickhouse

# 2. 复制配置文件
cp docker-compose.clickhouse.yaml docker-compose.yaml.clickhouse-backup

# 3. 创建初始化脚本
# （见下面的完整脚本）
```

### 阶段 2：代码实现（2小时）

1. 创建 ClickHouse 连接模块
2. 创建 ClickHouse CDR 模型
3. 更新 CDR 路由逻辑
4. 更新依赖包

### 阶段 3：测试验证（1小时）

1. 本地测试连接
2. 测试写入
3. 测试查询
4. 性能测试

### 阶段 4：部署上线（30分钟）

```bash
# 1. 停止现有服务
docker-compose down

# 2. 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# 3. 启动新架构
docker-compose -f docker-compose.clickhouse.yaml up -d

# 4. 查看日志
docker-compose -f docker-compose.clickhouse.yaml logs -f
```

## 📝 完整代码实现

### 1. ClickHouse 建表 SQL

创建文件：`clickhouse/init/01_create_tables.sql`

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS vos_cdrs;

-- 切换到数据库
USE vos_cdrs;

-- CDR 话单表（使用 ReplacingMergeTree 去重）
CREATE TABLE IF NOT EXISTS cdrs
(
    -- 基础字段
    id UInt64,
    vos_id UInt32,
    flow_no String,
    
    -- 账户信息
    account_name String,
    account String,
    
    -- 呼叫信息
    caller_e164 String,
    caller_access_e164 String,
    callee_e164 String,
    callee_access_e164 String,
    
    -- 时间信息（分区键）
    start DateTime,
    stop DateTime,
    
    -- 时长和费用
    hold_time UInt32,
    fee_time UInt32,
    fee Decimal(10, 4),
    
    -- 终止信息
    end_reason String,
    end_direction UInt8,
    
    -- 网关和IP
    callee_gateway String,
    callee_ip String,
    
    -- 原始数据
    raw String,
    
    -- 元数据
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(start)
ORDER BY (vos_id, start, flow_no)
SETTINGS index_granularity = 8192;

-- 创建索引
-- ClickHouse 使用 ORDER BY 作为主索引，以下是额外的优化

-- 账号查询优化
ALTER TABLE cdrs ADD INDEX idx_account account TYPE minmax GRANULARITY 4;

-- 主被叫号码查询优化
ALTER TABLE cdrs ADD INDEX idx_caller caller_e164 TYPE minmax GRANULARITY 4;
ALTER TABLE cdrs ADD INDEX idx_callee callee_access_e164 TYPE minmax GRANULARITY 4;

-- 网关查询优化
ALTER TABLE cdrs ADD INDEX idx_gateway callee_gateway TYPE minmax GRANULARITY 4;

-- 创建物化视图 - 按天统计
CREATE MATERIALIZED VIEW IF NOT EXISTS cdrs_daily_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(call_date)
ORDER BY (vos_id, call_date, account)
AS SELECT
    vos_id,
    toDate(start) AS call_date,
    account,
    count() AS call_count,
    sum(hold_time) AS total_duration,
    sum(fee) AS total_fee
FROM cdrs
GROUP BY vos_id, call_date, account;

-- 创建物化视图 - 按账户实时统计
CREATE MATERIALIZED VIEW IF NOT EXISTS cdrs_account_stats
ENGINE = SummingMergeTree()
ORDER BY (vos_id, account)
AS SELECT
    vos_id,
    account,
    count() AS call_count,
    sum(hold_time) AS total_duration,
    sum(fee) AS total_fee,
    max(start) AS last_call_time
FROM cdrs
GROUP BY vos_id, account;
```

### 2. ClickHouse Python 连接

创建文件：`backend/app/core/clickhouse_db.py`

```python
from clickhouse_driver import Client
from typing import Optional, List, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class ClickHouseDB:
    """ClickHouse 数据库连接管理"""
    
    def __init__(self):
        self.host = os.getenv('CLICKHOUSE_HOST', 'clickhouse')
        self.port = int(os.getenv('CLICKHOUSE_PORT', 9000))
        self.user = os.getenv('CLICKHOUSE_USER', 'vos_user')
        self.password = os.getenv('CLICKHOUSE_PASSWORD', 'vos_password')
        self.database = os.getenv('CLICKHOUSE_DATABASE', 'vos_cdrs')
        self.client: Optional[Client] = None
    
    def connect(self) -> Client:
        """创建连接"""
        if self.client is None:
            self.client = Client(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                settings={'use_numpy': False}
            )
            logger.info(f'ClickHouse 连接成功: {self.host}:{self.port}/{self.database}')
        return self.client
    
    def execute(self, query: str, params: Optional[Dict] = None) -> Any:
        """执行查询"""
        try:
            client = self.connect()
            result = client.execute(query, params or {})
            return result
        except Exception as e:
            logger.error(f'ClickHouse 查询失败: {e}')
            raise
    
    def insert(self, table: str, data: List[Dict], columns: Optional[List[str]] = None):
        """批量插入数据"""
        if not data:
            return
        
        try:
            client = self.connect()
            
            # 如果没有指定列，使用第一行的键
            if columns is None:
                columns = list(data[0].keys())
            
            # 准备数据
            values = [[row.get(col) for col in columns] for row in data]
            
            # 执行插入
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES"
            client.execute(query, values)
            
            logger.info(f'ClickHouse 插入成功: {len(data)} 条记录到 {table}')
        except Exception as e:
            logger.error(f'ClickHouse 插入失败: {e}')
            raise
    
    def close(self):
        """关闭连接"""
        if self.client:
            self.client.disconnect()
            self.client = None
            logger.info('ClickHouse 连接已关闭')

# 全局单例
ch_db = ClickHouseDB()

def get_clickhouse_client() -> Client:
    """获取 ClickHouse 客户端"""
    return ch_db.connect()
```

### 3. ClickHouse CDR 操作类

创建文件：`backend/app/models/clickhouse_cdr.py`

```python
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.clickhouse_db import ch_db
import logging

logger = logging.getLogger(__name__)

class ClickHouseCDR:
    """ClickHouse CDR 数据操作"""
    
    @staticmethod
    def insert_cdrs(cdrs: List[Dict]) -> int:
        """批量插入话单"""
        if not cdrs:
            return 0
        
        # 转换字段名（VOS API 格式 -> ClickHouse 格式）
        ch_cdrs = []
        for cdr in cdrs:
            ch_cdr = {
                'id': hash(cdr.get('flowNo', '')),  # 生成唯一ID
                'vos_id': cdr.get('vos_id', 0),
                'flow_no': cdr.get('flowNo', ''),
                'account_name': cdr.get('accountName', ''),
                'account': cdr.get('account', ''),
                'caller_e164': cdr.get('callerE164', ''),
                'caller_access_e164': cdr.get('callerAccessE164', ''),
                'callee_e164': cdr.get('calleeE164', ''),
                'callee_access_e164': cdr.get('calleeAccessE164', ''),
                'start': datetime.fromtimestamp(cdr.get('start', 0) / 1000) if cdr.get('start') else datetime.now(),
                'stop': datetime.fromtimestamp(cdr.get('stop', 0) / 1000) if cdr.get('stop') else None,
                'hold_time': cdr.get('holdTime', 0),
                'fee_time': cdr.get('feeTime', 0),
                'fee': float(cdr.get('fee', 0)),
                'end_reason': cdr.get('endReason', ''),
                'end_direction': cdr.get('endDirection', 0),
                'callee_gateway': cdr.get('calleeGateway', ''),
                'callee_ip': cdr.get('calleeip', ''),
                'raw': str(cdr),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            ch_cdrs.append(ch_cdr)
        
        # 批量插入
        ch_db.insert('cdrs', ch_cdrs)
        logger.info(f'成功插入 {len(ch_cdrs)} 条话单到 ClickHouse')
        return len(ch_cdrs)
    
    @staticmethod
    def query_cdrs(
        vos_id: int,
        start_date: datetime,
        end_date: datetime,
        accounts: Optional[List[str]] = None,
        caller_e164: Optional[str] = None,
        callee_e164: Optional[str] = None,
        callee_gateway: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> tuple[List[Dict], int]:
        """查询话单"""
        
        # 构建查询条件
        conditions = [
            f"vos_id = {vos_id}",
            f"start >= toDateTime('{start_date.strftime('%Y-%m-%d %H:%M:%S')}')",
            f"start < toDateTime('{end_date.strftime('%Y-%m-%d %H:%M:%S')}')"
        ]
        
        if accounts:
            accounts_str = "', '".join(accounts)
            conditions.append(f"account IN ('{accounts_str}')")
        
        if caller_e164:
            conditions.append(f"caller_e164 LIKE '%{caller_e164}%'")
        
        if callee_e164:
            conditions.append(f"callee_access_e164 LIKE '%{callee_e164}%'")
        
        if callee_gateway:
            conditions.append(f"callee_gateway = '{callee_gateway}'")
        
        where_clause = " AND ".join(conditions)
        
        # 查询总数
        count_query = f"SELECT count() FROM cdrs WHERE {where_clause}"
        total_count = ch_db.execute(count_query)[0][0]
        
        # 查询数据
        query = f"""
            SELECT 
                flow_no,
                account_name,
                account,
                caller_e164,
                caller_access_e164,
                callee_access_e164,
                callee_gateway,
                start,
                stop,
                hold_time,
                fee_time,
                fee,
                end_direction,
                end_reason
            FROM cdrs
            WHERE {where_clause}
            ORDER BY start DESC
            LIMIT {limit} OFFSET {offset}
        """
        
        rows = ch_db.execute(query)
        
        # 转换为字典列表
        cdrs = []
        for row in rows:
            cdrs.append({
                'flowNo': row[0],
                'accountName': row[1],
                'account': row[2],
                'callerE164': row[3],
                'callerAccessE164': row[4],
                'calleeAccessE164': row[5],
                'calleeGateway': row[6],
                'start': row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None,
                'stop': row[8].strftime('%Y-%m-%d %H:%M:%S') if row[8] else None,
                'holdTime': row[9],
                'feeTime': row[10],
                'fee': float(row[11]),
                'endDirection': row[12],
                'endReason': row[13]
            })
        
        return cdrs, total_count
    
    @staticmethod
    def get_stats(vos_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """获取统计信息"""
        query = f"""
            SELECT 
                count() as total_count,
                sum(hold_time) as total_duration,
                sum(fee) as total_fee
            FROM cdrs
            WHERE vos_id = {vos_id}
              AND start >= toDateTime('{start_date.strftime('%Y-%m-%d %H:%M:%S')}')
              AND start < toDateTime('{end_date.strftime('%Y-%m-%d %H:%M:%S')}')
        """
        
        result = ch_db.execute(query)[0]
        return {
            'total_count': result[0],
            'total_duration': result[1] or 0,
            'total_fee': float(result[2] or 0)
        }
```

### 4. 更新 requirements.txt

在 `backend/requirements.txt` 中添加：

```txt
clickhouse-driver>=0.2.6
```

### 5. 环境变量配置

创建 `.env` 文件（如果没有）：

```bash
# PostgreSQL (配置数据)
POSTGRES_USER=vos_user
POSTGRES_PASSWORD=vos_password
POSTGRES_DB=vosadmin

# ClickHouse (话单数据)
CLICKHOUSE_USER=vos_user
CLICKHOUSE_PASSWORD=vos_password
CLICKHOUSE_DATABASE=vos_cdrs

# Redis
REDIS_URL=redis://redis:6379

# 认证
SECRET_KEY=your-secret-key-change-in-production
```

## 🚀 快速开始

```bash
# 1. 创建必要的目录
mkdir -p clickhouse/init data/clickhouse

# 2. 复制 SQL 初始化脚本到 clickhouse/init/01_create_tables.sql

# 3. 更新依赖
cd backend
pip install clickhouse-driver

# 4. 启动服务
cd /data/yk-vos
docker-compose -f docker-compose.clickhouse.yaml up -d

# 5. 查看日志
docker-compose -f docker-compose.clickhouse.yaml logs -f clickhouse
docker-compose -f docker-compose.clickhouse.yaml logs -f backend
```

## ✅ 验证检查

```bash
# 1. 检查 ClickHouse 是否正常
docker-compose exec clickhouse clickhouse-client --query "SELECT 1"

# 2. 检查表是否创建
docker-compose exec clickhouse clickhouse-client --query "SHOW TABLES FROM vos_cdrs"

# 3. 测试插入数据
docker-compose exec clickhouse clickhouse-client --query "INSERT INTO vos_cdrs.cdrs (id, vos_id, flow_no, account, start) VALUES (1, 1, 'test123', 'test', now())"

# 4. 测试查询
docker-compose exec clickhouse clickhouse-client --query "SELECT * FROM vos_cdrs.cdrs LIMIT 10"
```

## 📊 性能优化建议

1. **批量插入**：每次插入至少 1000 条记录
2. **分区策略**：按月分区，保留 12 个月数据
3. **压缩算法**：使用 LZ4 压缩
4. **查询优化**：始终包含时间范围过滤
5. **物化视图**：预计算常用统计

## 🔧 故障排查

### ClickHouse 无法启动
```bash
# 检查日志
docker-compose logs clickhouse

# 检查权限
sudo chown -R 101:101 data/clickhouse
```

### 连接失败
```bash
# 测试网络连通性
docker-compose exec backend ping clickhouse

# 测试端口
docker-compose exec backend nc -zv clickhouse 9000
```

## 📚 参考资料

- [ClickHouse 官方文档](https://clickhouse.com/docs)
- [clickhouse-driver Python 文档](https://clickhouse-driver.readthedocs.io/)
- [ClickHouse 性能优化](https://clickhouse.com/docs/en/operations/optimization/)


