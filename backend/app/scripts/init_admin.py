#!/usr/bin/env python3
"""初始化管理员账号"""
import os
import sys
sys.path.insert(0, '/srv')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from app.models.user import User

pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')

# 获取数据库连接 URL，提供默认值
database_url = os.getenv('DATABASE_URL', 'postgresql://vos_user:vos_password@postgres:5432/vosadmin')
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)

def run():
    """只创建默认管理员账号，不预置VOS节点"""
    s = Session()
    if not s.query(User).filter(User.username=='admin').first():
        u = User(username='admin', hashed_password=pwd.hash('admin123'), is_active=True)
        s.add(u)
        print('✅ 已创建默认管理员账号: admin / admin123')
    else:
        print('ℹ️  管理员账号已存在，跳过创建')
    s.commit()
    s.close()

if __name__ == '__main__':
    run()
