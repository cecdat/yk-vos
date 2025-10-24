#!/usr/bin/env python3
"""
测试ClickHouse连接和话单同步
用于调试手动同步功能
"""
import sys
sys.path.insert(0, '/srv')

from app.core.config import settings
from app.models.clickhouse_cdr import ClickHouseCDR, get_clickhouse_db
from app.core.db import SessionLocal
from app.models.vos_instance import VOSInstance
from app.models.customer import Customer
from app.core.vos_client import VOSClient
from datetime import datetime, timedelta

def test_clickhouse_connection():
    """测试ClickHouse连接"""
    print("=" * 60)
    print("1. 测试 ClickHouse 连接")
    print("=" * 60)
    
    try:
        ch_db = get_clickhouse_db()
        result = ch_db.execute('SELECT version()')
        print(f"✅ ClickHouse 连接成功！")
        print(f"   版本: {result[0][0]}")
        
        # 检查 cdrs 表
        result = ch_db.execute('SELECT count() FROM cdrs')
        print(f"   cdrs 表记录数: {result[0][0]}")
        
        # 显示最近的话单
        result = ch_db.execute('SELECT vos_id, caller_e164, callee_e164, created_at FROM cdrs ORDER BY created_at DESC LIMIT 5')
        if result:
            print(f"\n   最近的话单记录:")
            for row in result:
                print(f"     - VOS#{row[0]}: {row[1]} → {row[2]} @ {row[3]}")
        else:
            print(f"\n   ⚠️ cdrs 表为空")
        
        return True
    except Exception as e:
        print(f"❌ ClickHouse 连接失败: {e}")
        return False


def test_vos_api_call():
    """测试VOS API调用"""
    print("\n" + "=" * 60)
    print("2. 测试 VOS API 调用")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        
        if not instances:
            print("❌ 没有启用的VOS实例")
            return False
        
        for inst in instances:
            print(f"\n📍 VOS实例: {inst.name}")
            print(f"   地址: {inst.base_url}")
            
            # 获取客户列表
            customers = db.query(Customer).filter(
                Customer.vos_instance_id == inst.id
            ).all()
            
            if not customers:
                print(f"   ⚠️ 该实例没有客户数据")
                continue
            
            print(f"   客户数: {len(customers)}")
            
            # 测试查询第一个客户的话单
            if customers:
                test_customer = customers[0]
                print(f"\n   测试查询客户: {test_customer.account}")
                
                client = VOSClient(inst.base_url)
                end = datetime.utcnow()
                start = end - timedelta(days=1)
                
                payload = {
                    'accounts': [test_customer.account],
                    'beginTime': start.strftime('%Y%m%d'),
                    'endTime': end.strftime('%Y%m%d')
                }
                
                try:
                    res = client.post('/external/server/GetCdr', payload=payload)
                    
                    if isinstance(res, dict):
                        if res.get('retCode') == 0:
                            cdrs = res.get('infoCdrs') or res.get('cdrs') or res.get('CDRList') or []
                            print(f"   ✅ API调用成功，返回 {len(cdrs) if isinstance(cdrs, list) else 0} 条话单")
                            
                            if cdrs and isinstance(cdrs, list) and len(cdrs) > 0:
                                print(f"\n   示例话单数据:")
                                sample = cdrs[0]
                                print(f"     主叫: {sample.get('callerE164') or sample.get('callerAccessE164')}")
                                print(f"     被叫: {sample.get('calleeE164') or sample.get('calleeAccessE164')}")
                                print(f"     开始时间: {sample.get('beginTime')}")
                                print(f"     通话时长: {sample.get('totalSeconds')}秒")
                        else:
                            print(f"   ❌ API返回错误: retCode={res.get('retCode')}, {res.get('exception')}")
                    else:
                        print(f"   ❌ API返回格式异常: {type(res)}")
                        
                except Exception as e:
                    print(f"   ❌ API调用失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        db.close()


def test_manual_sync():
    """测试手动同步"""
    print("\n" + "=" * 60)
    print("3. 测试手动同步到 ClickHouse")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        instances = db.query(VOSInstance).filter(VOSInstance.enabled == True).all()
        
        if not instances:
            print("❌ 没有启用的VOS实例")
            return False
        
        inst = instances[0]
        customers = db.query(Customer).filter(
            Customer.vos_instance_id == inst.id
        ).all()
        
        if not customers:
            print(f"❌ VOS实例 {inst.name} 没有客户数据")
            return False
        
        customer = customers[0]
        
        print(f"📍 同步测试")
        print(f"   VOS实例: {inst.name}")
        print(f"   客户: {customer.account}")
        
        # 查询话单
        client = VOSClient(inst.base_url)
        end = datetime.utcnow()
        start = end - timedelta(days=1)
        
        payload = {
            'accounts': [customer.account],
            'beginTime': start.strftime('%Y%m%d'),
            'endTime': end.strftime('%Y%m%d')
        }
        
        res = client.post('/external/server/GetCdr', payload=payload)
        
        if not isinstance(res, dict) or res.get('retCode') != 0:
            print(f"❌ VOS API调用失败")
            return False
        
        cdrs = res.get('infoCdrs') or res.get('cdrs') or res.get('CDRList') or []
        if not isinstance(cdrs, list):
            for v in res.values():
                if isinstance(v, list):
                    cdrs = v
                    break
        
        print(f"\n   从VOS获取到 {len(cdrs)} 条话单")
        
        if cdrs:
            print(f"   正在写入 ClickHouse...")
            inserted = ClickHouseCDR.insert_cdrs(cdrs, vos_id=inst.id)
            print(f"   ✅ 成功写入 {inserted} 条话单")
            
            # 验证写入
            ch_db = get_clickhouse_db()
            result = ch_db.execute(f'SELECT count() FROM cdrs WHERE vos_id = {inst.id}')
            total_count = result[0][0]
            print(f"   📊 ClickHouse中该VOS实例的话单总数: {total_count}")
            
            return True
        else:
            print(f"   ⚠️ 该客户在最近1天内没有话单")
            return True
            
    except Exception as e:
        print(f"❌ 同步测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == '__main__':
    print("\n🔍 ClickHouse 同步功能测试")
    print("=" * 60)
    
    success = True
    
    # 测试1: ClickHouse连接
    if not test_clickhouse_connection():
        success = False
    
    # 测试2: VOS API调用
    if not test_vos_api_call():
        success = False
    
    # 测试3: 手动同步
    if not test_manual_sync():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查上面的错误信息")
    print("=" * 60 + "\n")

