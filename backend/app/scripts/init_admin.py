#!/usr/bin/env python3
"""Seed admin user and demo VOS node"""
import os
import sys
sys.path.insert(0, '/srv')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from app.models.user import User
from app.models.vos_instance import VOSInstance
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
engine = create_engine(os.getenv('DATABASE_URL'))
Session = sessionmaker(bind=engine)
def run():
    s = Session()
    if not s.query(User).filter(User.username=='admin').first():
        u = User(username='admin', hashed_password=pwd.hash('admin123'), is_active=True)
        s.add(u)
    if not s.query(VOSInstance).filter(VOSInstance.base_url=='http://222.240.51.36:62020').first():
        v = VOSInstance(name='demo-vos', base_url='http://222.240.51.36:62020', description='Demo VOS node', enabled=True)
        s.add(v)
    s.commit()
    s.close()
if __name__ == '__main__':
    run()
