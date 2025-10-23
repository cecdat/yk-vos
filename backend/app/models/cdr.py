from sqlalchemy import Column, Integer, String, DateTime, Numeric, SmallInteger
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base


class CDR(Base):
    """
    话单记录表（基于TimescaleDB的超表）
    
    优化说明：
    - 使用TimescaleDB自动分区（按时间）
    - raw字段使用JSONB（自动压缩+支持JSON查询）
    - flowNo作为唯一标识（去重）
    """
    __tablename__ = 'cdrs'
    
    # 主键和外键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增主键')
    vos_id = Column(Integer, nullable=False, index=True, comment='VOS实例ID')
    
    # 账户信息
    account_name = Column(String(128), comment='账户名称')
    account = Column(String(64), index=True, comment='账户号码')
    
    # 呼叫信息
    caller_e164 = Column(String(64), index=True, comment='主叫号码')
    callee_access_e164 = Column(String(64), index=True, comment='被叫号码')
    
    # 时间信息（TimescaleDB主分区键）
    start = Column(DateTime, nullable=False, index=True, comment='起始时间')
    stop = Column(DateTime, comment='终止时间')
    
    # 时长和费用
    hold_time = Column(Integer, comment='通话时长(秒)')
    fee_time = Column(Integer, comment='计费时长(秒)')
    fee = Column(Numeric(10, 4), comment='通话费用')
    
    # 终止信息
    end_reason = Column(String(128), comment='终止原因')
    end_direction = Column(SmallInteger, comment='挂断方(0主叫，1被叫，2服务器)')
    
    # 网关和IP
    callee_gateway = Column(String(64), index=True, comment='主叫经由路由')
    callee_ip = Column(String(64), comment='被叫IP地址')
    
    # 原始数据和唯一标识
    raw = Column(JSONB, comment='原始话单数据(JSONB格式)')
    flow_no = Column(String(64), unique=True, nullable=False, index=True, comment='话单唯一标识')
    
    def __repr__(self):
        return f"<CDR(flow_no='{self.flow_no}', caller='{self.caller_e164}', start='{self.start}')>"
