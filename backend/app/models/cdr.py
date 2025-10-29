from sqlalchemy import Column, Integer, String, DateTime, Numeric, SmallInteger, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.models.base import Base


class CDR(Base):
    """
    话单记录表（基于TimescaleDB的超表）
    
    优化说明：
    - 使用TimescaleDB自动分区（按时间）
    - 复合主键(start, flow_no)满足TimescaleDB要求
    - raw字段使用JSONB（自动压缩+支持JSON查询）
    - flowNo作为唯一标识（去重）
    """
    __tablename__ = 'cdrs'
    __table_args__ = (
        PrimaryKeyConstraint('start', 'flow_no'),
        {'comment': 'VOS话单记录表（TimescaleDB超表）'}
    )
    
    # 基础字段
    id = Column(Integer, autoincrement=True, nullable=False, index=True, comment='自增ID（非主键，用于排序和引用）')
    vos_id = Column(Integer, nullable=False, index=True, comment='VOS实例ID')
    vos_uuid = Column(UUID(as_uuid=True), nullable=True, index=True, comment='VOS节点唯一标识')
    
    # 账户信息
    account_name = Column(String(128), comment='账户名称')
    account = Column(String(64), index=True, comment='账户号码')
    
    # 呼叫信息
    caller_e164 = Column(String(64), index=True, comment='主叫号码')
    callee_access_e164 = Column(String(64), index=True, comment='被叫号码')
    
    # 时间信息（TimescaleDB主分区键 + 主键之一）
    start = Column(DateTime, nullable=False, comment='起始时间（主键之一）')
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
    flow_no = Column(String(64), nullable=False, comment='话单唯一标识（主键之一）')
    
    def __repr__(self):
        return f"<CDR(flow_no='{self.flow_no}', caller='{self.caller_e164}', start='{self.start}')>"
