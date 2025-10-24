"""
ClickHouse CDR 数据操作模型
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from app.core.clickhouse_db import get_clickhouse_db
import logging
import hashlib

logger = logging.getLogger(__name__)


class ClickHouseCDR:
    """ClickHouse CDR 数据操作"""
    
    @staticmethod
    def _generate_id(flow_no) -> int:
        """根据 flow_no 生成唯一 ID"""
        if not flow_no:
            return 0
        # 确保 flow_no 是字符串类型
        flow_no_str = str(flow_no)
        # 使用 MD5 哈希前8字节转为整数
        hash_obj = hashlib.md5(flow_no_str.encode())
        return int(hash_obj.hexdigest()[:16], 16)
    
    @staticmethod
    def insert_cdrs(cdrs: List[Dict], vos_id: Optional[int] = None) -> int:
        """批量插入话单
        
        Args:
            cdrs: 话单列表（VOS API 格式）
            vos_id: VOS 实例 ID（如果 CDR 中没有则使用此值）
            
        Returns:
            成功插入的记录数
        """
        if not cdrs:
            return 0
        
        ch_db = get_clickhouse_db()
        
        # 转换字段名（VOS API 格式 -> ClickHouse 格式）
        ch_cdrs = []
        for cdr in cdrs:
            # 获取 VOS ID
            cdr_vos_id = cdr.get('vos_id', vos_id or 0)
            
            # 时间处理
            start_time = cdr.get('start')
            stop_time = cdr.get('stop')
            
            if start_time and isinstance(start_time, (int, float)):
                start_dt = datetime.fromtimestamp(start_time / 1000)
            else:
                start_dt = datetime.now()
            
            if stop_time and isinstance(stop_time, (int, float)):
                stop_dt = datetime.fromtimestamp(stop_time / 1000)
            else:
                stop_dt = None
            
            flow_no = cdr.get('flowNo', '')
            # 确保 flow_no 是字符串类型
            flow_no_str = str(flow_no) if flow_no else ''
            
            ch_cdr = {
                'id': ClickHouseCDR._generate_id(flow_no_str),
                'vos_id': cdr_vos_id,
                'flow_no': flow_no_str,
                'account_name': cdr.get('accountName', ''),
                'account': cdr.get('account', ''),
                'caller_e164': cdr.get('callerE164', ''),
                'caller_access_e164': cdr.get('callerAccessE164', ''),
                'callee_e164': cdr.get('calleeE164', ''),
                'callee_access_e164': cdr.get('calleeAccessE164', ''),
                'start': start_dt,
                'stop': stop_dt,
                'hold_time': int(cdr.get('holdTime', 0)),
                'fee_time': int(cdr.get('feeTime', 0)),
                'fee': float(cdr.get('fee', 0)),
                'end_reason': cdr.get('endReason', ''),
                'end_direction': int(cdr.get('endDirection', 0)),
                'callee_gateway': cdr.get('calleeGateway', ''),
                'callee_ip': cdr.get('calleeip', ''),
                'raw': str(cdr),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            ch_cdrs.append(ch_cdr)
        
        # 批量插入
        try:
            count = ch_db.insert('cdrs', ch_cdrs)
            logger.info(f'✅ 成功插入 {count} 条话单到 ClickHouse (VOS ID: {vos_id})')
            return count
        except Exception as e:
            logger.error(f'❌ 插入话单失败: {e}')
            return 0
    
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
    ) -> Tuple[List[Dict], int]:
        """查询话单
        
        Returns:
            (话单列表, 总数)
        """
        ch_db = get_clickhouse_db()
        
        # 构建查询条件
        conditions = [
            f"vos_id = {vos_id}",
            f"start >= toDateTime('{start_date.strftime('%Y-%m-%d %H:%M:%S')}')",
            f"start < toDateTime('{end_date.strftime('%Y-%m-%d %H:%M:%S')}')"
        ]
        
        if accounts:
            # 转义单引号
            accounts_escaped = ["'" + acc.replace("'", "\\'") + "'" for acc in accounts]
            accounts_str = ", ".join(accounts_escaped)
            conditions.append(f"account IN ({accounts_str})")
        
        if caller_e164:
            caller_escaped = caller_e164.replace("'", "\\'")
            conditions.append(f"(caller_e164 LIKE '%{caller_escaped}%' OR caller_access_e164 LIKE '%{caller_escaped}%')")
        
        if callee_e164:
            callee_escaped = callee_e164.replace("'", "\\'")
            conditions.append(f"callee_access_e164 LIKE '%{callee_escaped}%'")
        
        if callee_gateway:
            gateway_escaped = callee_gateway.replace("'", "\\'")
            conditions.append(f"callee_gateway = '{gateway_escaped}'")
        
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
                end_reason,
                callee_ip
            FROM cdrs
            WHERE {where_clause}
            ORDER BY start DESC
            LIMIT {limit} OFFSET {offset}
        """
        
        rows = ch_db.execute(query)
        
        # 转换为字典列表（返回 VOS API 格式）
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
                'start': int(row[7].timestamp() * 1000) if row[7] else None,  # 转为毫秒时间戳
                'stop': int(row[8].timestamp() * 1000) if row[8] else None,
                'holdTime': row[9],
                'feeTime': row[10],
                'fee': float(row[11]),
                'endDirection': row[12],
                'endReason': row[13],
                'calleeip': row[14]
            })
        
        return cdrs, total_count
    
    @staticmethod
    def get_stats(vos_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """获取统计信息"""
        ch_db = get_clickhouse_db()
        
        query = f"""
            SELECT 
                count() as total_count,
                sum(hold_time) as total_duration,
                sum(fee) as total_fee,
                countDistinct(account) as unique_accounts
            FROM cdrs
            WHERE vos_id = {vos_id}
              AND start >= toDateTime('{start_date.strftime('%Y-%m-%d %H:%M:%S')}')
              AND start < toDateTime('{end_date.strftime('%Y-%m-%d %H:%M:%S')}')
        """
        
        result = ch_db.execute(query)[0]
        return {
            'total_count': result[0],
            'total_duration': result[1] or 0,
            'total_fee': float(result[2] or 0),
            'unique_accounts': result[3]
        }
    
    @staticmethod
    def get_total_count(vos_id: Optional[int] = None) -> int:
        """获取话单总数"""
        ch_db = get_clickhouse_db()
        
        if vos_id:
            query = f"SELECT count() FROM cdrs WHERE vos_id = {vos_id}"
        else:
            query = "SELECT count() FROM cdrs"
        
        result = ch_db.execute(query)
        return result[0][0]
    
    @staticmethod
    def get_sync_status(vos_id: int) -> Tuple[int, Optional[datetime]]:
        """获取指定VOS实例的话单同步状态
        
        Returns:
            (total_count, last_sync_time): 总记录数和最后同步时间
        """
        try:
            ch_db = get_clickhouse_db()
            
            # 查询总记录数和最后同步时间
            query = f"""
                SELECT 
                    count() as count,
                    MAX(created_at) as last_sync
                FROM cdrs
                WHERE vos_id = {vos_id}
            """
            result = ch_db.execute(query)
            
            if result and result[0]:
                total_count = result[0][0]
                last_sync = result[0][1]
                return (total_count, last_sync)
            else:
                return (0, None)
                
        except Exception as e:
            logger.error(f'获取同步状态失败 (vos_id={vos_id}): {e}')
            return (0, None)
    
    @staticmethod
    def delete_old_partitions(months_to_keep: int = 12) -> List[str]:
        """删除旧分区（保留最近 N 个月）
        
        Args:
            months_to_keep: 保留的月数
            
        Returns:
            删除的分区列表
        """
        ch_db = get_clickhouse_db()
        
        # 计算截止日期
        cutoff_date = datetime.now() - timedelta(days=months_to_keep * 30)
        cutoff_partition = cutoff_date.strftime('%Y%m')
        
        # 获取所有旧分区
        query = f"""
            SELECT DISTINCT partition 
            FROM system.parts 
            WHERE database = 'vos_cdrs' 
              AND table = 'cdrs' 
              AND partition < '{cutoff_partition}'
              AND active
        """
        
        partitions = ch_db.execute(query)
        deleted_partitions = []
        
        for partition_tuple in partitions:
            partition = partition_tuple[0]
            try:
                drop_query = f"ALTER TABLE cdrs DROP PARTITION '{partition}'"
                ch_db.execute(drop_query)
                deleted_partitions.append(partition)
                logger.info(f'✅ 删除分区: {partition}')
            except Exception as e:
                logger.error(f'❌ 删除分区失败 {partition}: {e}')
        
        return deleted_partitions

