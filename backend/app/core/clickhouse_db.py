"""
ClickHouse 数据库连接模块
"""
from clickhouse_driver import Client
from typing import Optional, List, Dict, Any, Tuple
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
        self._connected = False
    
    def connect(self) -> Client:
        """创建连接"""
        if self.client is None or not self._connected:
            try:
                self.client = Client(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    settings={'use_numpy': False}
                )
                # 测试连接
                self.client.execute('SELECT 1')
                self._connected = True
                logger.info(f'✅ ClickHouse 连接成功: {self.host}:{self.port}/{self.database}')
            except Exception as e:
                logger.error(f'❌ ClickHouse 连接失败: {e}')
                raise
        return self.client
    
    def execute(self, query: str, params: Optional[Dict] = None, with_column_types: bool = False) -> Any:
        """执行查询"""
        try:
            client = self.connect()
            result = client.execute(query, params or {}, with_column_types=with_column_types)
            return result
        except Exception as e:
            logger.error(f'❌ ClickHouse 查询失败: {e}')
            logger.error(f'   查询语句: {query}')
            raise
    
    def insert(self, table: str, data: List[Dict], columns: Optional[List[str]] = None) -> int:
        """批量插入数据"""
        if not data:
            return 0
        
        try:
            client = self.connect()
            
            # 如果没有指定列，使用第一行的键
            if columns is None:
                columns = list(data[0].keys())
            
            # 准备数据 - 确保所有值类型正确
            values = []
            for row in data:
                row_values = []
                for col in columns:
                    val = row.get(col)
                    # 确保字符串类型的字段不会是None
                    if val is None:
                        if col in ['flow_no', 'account_name', 'account', 'caller_e164', 
                                   'caller_access_e164', 'callee_e164', 'callee_access_e164',
                                   'end_reason', 'callee_gateway', 'callee_ip', 'raw']:
                            val = ''
                        elif col in ['hold_time', 'fee_time', 'end_direction', 'vos_id', 'id']:
                            val = 0
                        elif col == 'fee':
                            val = 0.0
                    row_values.append(val)
                values.append(row_values)
            
            # 执行插入
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES"
            client.execute(query, values)
            
            logger.info(f'✅ ClickHouse 插入成功: {len(data)} 条记录到 {table}')
            return len(data)
        except Exception as e:
            logger.error(f'❌ ClickHouse 插入失败: {e}')
            logger.error(f'   表名: {table}, 数据量: {len(data)}')
            # 打印第一条数据的详细信息用于调试
            if data:
                logger.error(f'   第一条数据示例:')
                for k, v in list(data[0].items())[:5]:
                    logger.error(f'     {k}: {v} (type: {type(v).__name__})')
            raise
    
    def close(self):
        """关闭连接"""
        if self.client:
            try:
                self.client.disconnect()
                self._connected = False
                logger.info('ClickHouse 连接已关闭')
            except:
                pass
            finally:
                self.client = None
    
    def ping(self) -> bool:
        """测试连接是否正常"""
        try:
            result = self.execute('SELECT 1')
            return result[0][0] == 1
        except:
            return False


# 全局单例
_ch_db_instance = None


def get_clickhouse_db() -> ClickHouseDB:
    """获取 ClickHouse 数据库实例（单例模式）"""
    global _ch_db_instance
    if _ch_db_instance is None:
        _ch_db_instance = ClickHouseDB()
    return _ch_db_instance


def get_clickhouse_client() -> Client:
    """获取 ClickHouse 客户端"""
    return get_clickhouse_db().connect()

