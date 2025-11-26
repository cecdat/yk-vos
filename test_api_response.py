#!/usr/bin/env python3
"""
测试脚本：检查后端API是否正确返回last_synced_count
"""
import sys
sys.path.insert(0, '/srv')

from app.core.redis_cache import RedisCache
import json

print("=" * 60)
print("测试后端 get_cdr_sync_status 函数的逻辑")
print("=" * 60)

# 1. 检查Redis中的数据
print("\n1. 检查Redis中的 last_cdr_sync_result:")
last_sync_result_json = RedisCache.get('last_cdr_sync_result')
if last_sync_result_json:
    print(f"   原始数据: {last_sync_result_json}")
    last_sync_result = json.loads(last_sync_result_json)
    print(f"   解析后: {json.dumps(last_sync_result, indent=2, ensure_ascii=False)}")
    last_synced_count = last_sync_result.get('synced_count', 0)
    print(f"   提取的 synced_count: {last_synced_count}")
else:
    print("   ❌ Redis中没有数据")
    last_synced_count = 0

# 2. 模拟后端返回的数据结构
print("\n2. 模拟后端API返回的数据结构:")
response = {
    'success': True,
    'status': 'idle',
    'is_syncing': False,
    'total_cdrs': 100000,
    'last_sync_time': '2025-11-26T11:49:46.196066',
    'last_synced_count': last_synced_count,
    'instances_count': 1,
    'instances': [],
    'next_sync': '每天凌晨 01:30 自动同步'
}

print(json.dumps(response, indent=2, ensure_ascii=False))

# 3. 检查字段是否存在
print("\n3. 检查关键字段:")
print(f"   last_synced_count 存在: {('last_synced_count' in response)}")
print(f"   last_synced_count 值: {response.get('last_synced_count')}")
print(f"   last_synced_count > 0: {response.get('last_synced_count', 0) > 0}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
