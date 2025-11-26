#!/usr/bin/env python3
"""
清理ClickHouse中的重复话单数据

原理：
1. ClickHouse中的话单使用 flow_no 的MD5哈希作为唯一ID
2. 如果同一个 flow_no 被插入多次，会有多条相同ID的记录
3. 使用 OPTIMIZE TABLE ... FINAL DEDUPLICATE 来去重

使用方法：
1. 先查看重复数据统计
2. 确认后执行去重操作
"""
import sys
sys.path.insert(0, '/srv')

from app.core.clickhouse_db import get_clickhouse_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_duplicates():
    """检查重复数据"""
    ch_db = get_clickhouse_db()
    
    print("=" * 80)
    print("检查重复话单数据")
    print("=" * 80)
    
    # 1. 统计总记录数
    total_query = "SELECT count() FROM cdrs"
    total_count = ch_db.execute(total_query)[0][0]
    print(f"\n1. 总记录数: {total_count:,}")
    
    # 2. 统计唯一ID数量
    unique_query = "SELECT count(DISTINCT id) FROM cdrs"
    unique_count = ch_db.execute(unique_query)[0][0]
    print(f"2. 唯一ID数量: {unique_count:,}")
    
    # 3. 计算重复数量
    duplicate_count = total_count - unique_count
    print(f"3. 重复记录数: {duplicate_count:,}")
    
    if duplicate_count == 0:
        print("\n✅ 没有重复数据！")
        return False
    
    # 4. 查看重复最多的记录
    print(f"\n4. 重复最多的前10条记录：")
    duplicate_query = """
        SELECT 
            id,
            flow_no,
            account,
            count() as cnt,
            min(start) as first_start,
            max(start) as last_start
        FROM cdrs
        GROUP BY id, flow_no, account
        HAVING cnt > 1
        ORDER BY cnt DESC
        LIMIT 10
    """
    duplicates = ch_db.execute(duplicate_query)
    
    print(f"\n{'ID':<20} {'FlowNo':<20} {'Account':<15} {'重复次数':<10} {'首次时间':<20} {'最后时间':<20}")
    print("-" * 120)
    for row in duplicates:
        print(f"{row[0]:<20} {row[1]:<20} {row[2]:<15} {row[3]:<10} {str(row[4]):<20} {str(row[5]):<20}")
    
    # 5. 按VOS实例统计重复情况
    print(f"\n5. 各VOS实例重复情况：")
    vos_duplicate_query = """
        SELECT 
            vos_id,
            count() as total_records,
            count(DISTINCT id) as unique_records,
            count() - count(DISTINCT id) as duplicate_records
        FROM cdrs
        GROUP BY vos_id
        ORDER BY duplicate_records DESC
    """
    vos_stats = ch_db.execute(vos_duplicate_query)
    
    print(f"\n{'VOS ID':<10} {'总记录数':<15} {'唯一记录数':<15} {'重复记录数':<15}")
    print("-" * 60)
    for row in vos_stats:
        print(f"{row[0]:<10} {row[1]:<15,} {row[2]:<15,} {row[3]:<15,}")
    
    print("\n" + "=" * 80)
    return True

def deduplicate_data(dry_run=True):
    """去重数据
    
    Args:
        dry_run: 如果为True，只显示将要执行的操作，不实际执行
    """
    ch_db = get_clickhouse_db()
    
    print("\n" + "=" * 80)
    if dry_run:
        print("去重操作预览（DRY RUN模式）")
    else:
        print("执行去重操作")
    print("=" * 80)
    
    # ClickHouse去重方法：
    # 方法1：使用 OPTIMIZE TABLE ... FINAL DEDUPLICATE BY id
    # 这会保留每个ID的第一条记录，删除后续重复的记录
    
    deduplicate_query = "OPTIMIZE TABLE cdrs FINAL DEDUPLICATE BY id"
    
    print(f"\n将执行SQL: {deduplicate_query}")
    
    if dry_run:
        print("\n⚠️ 这是预览模式，不会实际执行去重操作")
        print("如果确认要执行，请运行: python clean_duplicate_cdrs.py --execute")
    else:
        print("\n⚠️ 正在执行去重操作，这可能需要几分钟...")
        try:
            ch_db.execute(deduplicate_query)
            print("✅ 去重操作完成！")
            
            # 重新检查
            print("\n重新检查数据...")
            check_duplicates()
        except Exception as e:
            print(f"❌ 去重操作失败: {e}")
            return False
    
    return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='清理ClickHouse中的重复话单数据')
    parser.add_argument('--execute', action='store_true', help='实际执行去重操作（默认只预览）')
    parser.add_argument('--check-only', action='store_true', help='只检查重复数据，不执行去重')
    
    args = parser.parse_args()
    
    # 检查重复数据
    has_duplicates = check_duplicates()
    
    if not has_duplicates:
        print("\n没有需要清理的重复数据。")
        return
    
    if args.check_only:
        print("\n只检查模式，不执行去重操作。")
        return
    
    # 执行去重
    print("\n" + "=" * 80)
    if args.execute:
        confirm = input("\n⚠️ 确认要执行去重操作吗？这将删除重复的话单记录。(yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消操作。")
            return
        deduplicate_data(dry_run=False)
    else:
        deduplicate_data(dry_run=True)

if __name__ == '__main__':
    main()
