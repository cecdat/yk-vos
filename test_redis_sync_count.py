#!/usr/bin/env python3
"""
测试脚本：设置Redis中的last_cdr_sync_result数据
用于验证仪表盘是否能正确显示最近同步数量
"""
import redis
import json
from datetime import datetime

# 连接Redis（根据实际配置修改）
REDIS_URL = "redis://localhost:6379/0"
r = redis.from_url(REDIS_URL)

# 设置测试数据
test_data = {
    'synced_count': 12500,  # 测试数量：1.25万
    'sync_time': datetime.now().isoformat(),
    'duration': 120.5,
    'status': 'success'
}

# 保存到Redis
r.set('last_cdr_sync_result', json.dumps(test_data, ensure_ascii=False))

print("✅ 已设置测试数据到Redis:")
print(json.dumps(test_data, indent=2, ensure_ascii=False))

# 验证读取
result = r.get('last_cdr_sync_result')
if result:
    print("\n✅ 验证读取成功:")
    print(json.dumps(json.loads(result), indent=2, ensure_ascii=False))
else:
    print("\n❌ 读取失败")
