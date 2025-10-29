#!/usr/bin/env python3
"""
VOS节点管理工具
支持通过UUID管理VOS节点，处理IP变更等场景
"""

import os
import sys
import uuid
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.db import engine
from backend.app.models.vos_instance import VOSInstance
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

def list_vos_instances():
    """列出所有VOS实例"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        instances = db.query(VOSInstance).all()
        
        print("VOS实例列表:")
        print("-" * 80)
        print(f"{'ID':<4} {'UUID':<36} {'名称':<20} {'URL':<30} {'状态':<8}")
        print("-" * 80)
        
        for inst in instances:
            status = "启用" if inst.enabled else "禁用"
            print(f"{inst.id:<4} {str(inst.vos_uuid):<36} {inst.name:<20} {inst.base_url:<30} {status:<8}")
        
        print("-" * 80)
        print(f"总计: {len(instances)} 个实例")
        
    finally:
        db.close()

def update_vos_ip(vos_uuid_str: str, new_ip: str, new_port: int = 8080):
    """更新VOS实例的IP地址"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        vos_uuid = uuid.UUID(vos_uuid_str)
        instance = db.query(VOSInstance).filter(VOSInstance.vos_uuid == vos_uuid).first()
        
        if not instance:
            print(f"❌ 未找到UUID为 {vos_uuid_str} 的VOS实例")
            return False
        
        old_url = instance.base_url
        new_url = f"http://{new_ip}:{new_port}"
        
        print(f"更新VOS实例: {instance.name}")
        print(f"  旧地址: {old_url}")
        print(f"  新地址: {new_url}")
        
        # 确认更新
        confirm = input("确认更新? (y/N): ")
        if confirm.lower() != 'y':
            print("取消更新")
            return False
        
        instance.base_url = new_url
        db.commit()
        
        print(f"✅ 成功更新VOS实例 {instance.name} 的IP地址")
        return True
        
    except ValueError:
        print(f"❌ 无效的UUID格式: {vos_uuid_str}")
        return False
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def add_vos_instance(name: str, base_url: str, description: str = "", api_user: str = "", api_password: str = ""):
    """添加新的VOS实例"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 检查是否已存在相同URL的实例
        existing = db.query(VOSInstance).filter(VOSInstance.base_url == base_url).first()
        if existing:
            print(f"❌ 已存在相同URL的VOS实例: {existing.name} (UUID: {existing.vos_uuid})")
            return False
        
        # 创建新实例
        new_instance = VOSInstance(
            name=name,
            base_url=base_url,
            description=description,
            api_user=api_user,
            api_password=api_password,
            enabled=True
        )
        
        db.add(new_instance)
        db.commit()
        
        print(f"✅ 成功添加VOS实例: {name}")
        print(f"  UUID: {new_instance.vos_uuid}")
        print(f"  URL: {base_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ 添加失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def disable_vos_instance(vos_uuid_str: str):
    """禁用VOS实例"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        vos_uuid = uuid.UUID(vos_uuid_str)
        instance = db.query(VOSInstance).filter(VOSInstance.vos_uuid == vos_uuid).first()
        
        if not instance:
            print(f"❌ 未找到UUID为 {vos_uuid_str} 的VOS实例")
            return False
        
        if not instance.enabled:
            print(f"VOS实例 {instance.name} 已经是禁用状态")
            return True
        
        instance.enabled = False
        db.commit()
        
        print(f"✅ 成功禁用VOS实例: {instance.name}")
        return True
        
    except ValueError:
        print(f"❌ 无效的UUID格式: {vos_uuid_str}")
        return False
    except Exception as e:
        print(f"❌ 禁用失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def enable_vos_instance(vos_uuid_str: str):
    """启用VOS实例"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        vos_uuid = uuid.UUID(vos_uuid_str)
        instance = db.query(VOSInstance).filter(VOSInstance.vos_uuid == vos_uuid).first()
        
        if not instance:
            print(f"❌ 未找到UUID为 {vos_uuid_str} 的VOS实例")
            return False
        
        if instance.enabled:
            print(f"VOS实例 {instance.name} 已经是启用状态")
            return True
        
        instance.enabled = True
        db.commit()
        
        print(f"✅ 成功启用VOS实例: {instance.name}")
        return True
        
    except ValueError:
        print(f"❌ 无效的UUID格式: {vos_uuid_str}")
        return False
    except Exception as e:
        print(f"❌ 启用失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def show_help():
    """显示帮助信息"""
    print("""
VOS节点管理工具

用法:
  python vos_manager.py list                           # 列出所有VOS实例
  python vos_manager.py update <uuid> <new_ip> [port]  # 更新VOS实例IP地址
  python vos_manager.py add <name> <url> [desc]       # 添加新的VOS实例
  python vos_manager.py disable <uuid>                 # 禁用VOS实例
  python vos_manager.py enable <uuid>                  # 启用VOS实例
  python vos_manager.py help                          # 显示帮助

示例:
  python vos_manager.py list
  python vos_manager.py update 12345678-1234-1234-1234-123456789abc 192.168.1.100
  python vos_manager.py add "测试VOS" "http://192.168.1.100:8080" "测试环境"
  python vos_manager.py disable 12345678-1234-1234-1234-123456789abc
""")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_vos_instances()
    
    elif command == "update":
        if len(sys.argv) < 4:
            print("❌ 用法: python vos_manager.py update <uuid> <new_ip> [port]")
            return
        
        vos_uuid = sys.argv[2]
        new_ip = sys.argv[3]
        new_port = int(sys.argv[4]) if len(sys.argv) > 4 else 8080
        
        update_vos_ip(vos_uuid, new_ip, new_port)
    
    elif command == "add":
        if len(sys.argv) < 4:
            print("❌ 用法: python vos_manager.py add <name> <url> [desc]")
            return
        
        name = sys.argv[2]
        url = sys.argv[3]
        desc = sys.argv[4] if len(sys.argv) > 4 else ""
        
        add_vos_instance(name, url, desc)
    
    elif command == "disable":
        if len(sys.argv) < 3:
            print("❌ 用法: python vos_manager.py disable <uuid>")
            return
        
        vos_uuid = sys.argv[2]
        disable_vos_instance(vos_uuid)
    
    elif command == "enable":
        if len(sys.argv) < 3:
            print("❌ 用法: python vos_manager.py enable <uuid>")
            return
        
        vos_uuid = sys.argv[2]
        enable_vos_instance(vos_uuid)
    
    elif command == "help":
        show_help()
    
    else:
        print(f"❌ 未知命令: {command}")
        show_help()

if __name__ == "__main__":
    main()
