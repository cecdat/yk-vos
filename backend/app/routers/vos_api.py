"""
VOS API 通用路由处理器
为所有 37 个 VOS 接口提供统一的缓存查询逻辑
"""
from typing import Annotated, Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import logging

from app.core.db import get_db
from app.core.vos_cache_service import VosCacheService
from app.models.user import User
from app.models.vos_instance import VOSInstance
from app.routers.auth import get_current_user

router = APIRouter(prefix='/vos-api', tags=['vos-api'])
logger = logging.getLogger(__name__)


# ==================== Pydantic 请求模型 ====================

class GetCustomerRequest(BaseModel):
    """查询账户"""
    accounts: List[str] = Field(..., description="账户号码列表")

class GetAllCustomersRequest(BaseModel):
    """获取所有账户账号"""
    type: int = Field(..., description="0: 获取账号列表, 1: 获取简要信息")

class GetPayHistoryRequest(BaseModel):
    """查询缴费记录"""
    account: str = Field(..., description="账户号码")
    beginTime: str = Field(..., description="开始时间 (格式: YYYYMMDD)")
    endTime: str = Field(..., description="结束时间 (格式: YYYYMMDD)")

class GetConsumptionRequest(BaseModel):
    """查询其它收入记录"""
    account: str
    beginTime: str
    endTime: str

class GetCustomerPhoneBookRequest(BaseModel):
    """查询账户电话簿"""
    account: str

class GetPhoneRequest(BaseModel):
    """查询话机"""
    e164s: List[str] = Field(..., description="话机号码列表")

class GetPhoneOnlineRequest(BaseModel):
    """查询在线话机"""
    e164s: List[str] = Field(default_factory=list, description="话机号码列表")

class GetAllPhoneOnlineRequest(BaseModel):
    """获取所有在线话机"""
    pass

class GetGatewayMappingRequest(BaseModel):
    """查询对接网关"""
    names: List[str] = Field(default_factory=list, description="网关名称列表，空数组表示查询所有")

class GetGatewayMappingOnlineRequest(BaseModel):
    """查询在线对接网关"""
    names: List[str] = Field(default_factory=list)

class GetGatewayRoutingRequest(BaseModel):
    """查询落地网关"""
    names: List[str] = Field(default_factory=list)

class GetGatewayRoutingOnlineRequest(BaseModel):
    """查询在线落地网关"""
    names: List[str] = Field(default_factory=list)

class GetCurrentCallRequest(BaseModel):
    """查询当前通话"""
    callerE164s: List[str] = Field(default_factory=list)
    calleeE164s: List[str] = Field(default_factory=list)

class GetCdrRequest(BaseModel):
    """查询历史话单"""
    accounts: List[str] = Field(default_factory=list)
    beginTime: str
    endTime: str

class GetAvailableTimeRequest(BaseModel):
    """获取可用通话时长"""
    billingName: str
    billingMode: int
    calleeE164: str

class GetIvrSecondAvailableTimeRequest(BaseModel):
    """获取IVR第二路可用通话时长"""
    billingNumber: str
    billingType: int
    calleeE164: str
    firstE164: str
    firstConnectTime: int

class GetFeeRateGroupRequest(BaseModel):
    """查询费率组"""
    names: List[str] = Field(default_factory=list)

class GetFeeRateRequest(BaseModel):
    """查询费率"""
    feeRateGroup: str
    areaCodes: List[str] = Field(default_factory=list)

class GetSuiteRequest(BaseModel):
    """查询套餐"""
    ids: List[Any] = Field(default_factory=list)

class GetSuiteOrderRequest(BaseModel):
    """查询套餐订单"""
    ownerName: str
    ownerType: int = Field(..., description="2: 账户, 6: 话机")

class GetCurrentSuiteRequest(BaseModel):
    """查询生效套餐"""
    ownerName: str
    ownerType: int

class GetActivePhoneCardRequest(BaseModel):
    """查询在用电话卡"""
    pins: List[str] = Field(default_factory=list)

class GetBindedE164Request(BaseModel):
    """查询绑定号码"""
    pin: str

class GetPhoneCardRequest(BaseModel):
    """查询电话卡"""
    pin: str
    password: str

class GetReportCustomerFeeRequest(BaseModel):
    """查询账户明细报表"""
    accounts: List[str]
    period: int = Field(..., description="-2: 按月统计")
    beginTime: str
    endTime: str

class GetReportPhoneFeeRequest(BaseModel):
    """查询话机明细报表"""
    account: str
    period: int
    beginTime: str
    endTime: str

class GetReportCustomerLocationFeeRequest(BaseModel):
    """查询账户地区明细报表"""
    account: str
    period: int
    beginTime: str
    endTime: str

class GetE164ConvertRequest(BaseModel):
    """查询号码变换表"""
    account: str

class GetSoftSwitchRequest(BaseModel):
    """查询软交换"""
    pass

class GetPerformanceRequest(BaseModel):
    """查询性能"""
    pass

class GetAlarmCurrentRequest(BaseModel):
    """获取当前告警"""
    pass

class GetIvrAudioRequest(BaseModel):
    """获取IVR语音"""
    type: int


# ==================== 通用响应模型 ====================

class VosApiResponse(BaseModel):
    """VOS API 统一响应格式"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    data_source: str = Field(..., description="数据来源: database, vos_api, error")
    synced_at: Optional[str] = None
    instance_name: str


# ==================== 通用查询函数 ====================

async def query_vos_api(
    instance_id: int,
    api_path: str,
    params: Dict[str, Any],
    db: Session,
    refresh: bool = False
) -> Dict[str, Any]:
    """
    通用的VOS API查询函数
    实现三级缓存：Redis → PostgreSQL → VOS API
    """
    # 特殊处理：对于网关、费率组等API，空数组参数需要发送空对象
    special_apis = [
        '/external/server/GetGatewayMapping',
        '/external/server/GetGatewayMappingOnline',
        '/external/server/GetGatewayRouting',
        '/external/server/GetGatewayRoutingOnline',
        '/external/server/GetFeeRateGroup',
        '/external/server/GetSuite'
    ]
    
    if api_path in special_apis:
        # 过滤空数组参数
        filtered_params = {k: v for k, v in params.items() if not (isinstance(v, list) and len(v) == 0)}
        # 如果过滤后参数为空，传空字典
        params = filtered_params if filtered_params else {}
    
    # 验证VOS实例
    instance = db.query(VOSInstance).filter(VOSInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail='VOS实例不存在')
    
    # 使用缓存服务查询数据
    cache_service = VosCacheService(db)
    data, source = cache_service.get_cached_data(
        vos_instance_id=instance_id,
        api_path=api_path,
        params=params,
        force_refresh=refresh
    )
    
    # 如果获取数据失败，返回错误
    if source == 'error' or data is None:
        return {
            'success': False,
            'data': None,
            'error': '从VOS获取数据失败',
            'data_source': source,
            'synced_at': None,
            'instance_name': instance.name
        }
    
    # 获取同步时间
    from app.models.vos_data_cache import VosDataCache
    cache_key = VosCacheService.generate_cache_key(api_path, params)
    cached = db.query(VosDataCache).filter(
        VosDataCache.vos_instance_id == instance_id,
        VosDataCache.api_path == api_path,
        VosDataCache.cache_key == cache_key
    ).first()
    
    synced_at = cached.synced_at.isoformat() if cached and cached.synced_at else None
    
    # 直接返回VOS原始数据（保持原有接口兼容性）
    # 这样前端可以直接使用 res.data.gatewayMappings, res.data.retCode 等
    return data


# ==================== 路由处理器 ====================

@router.post('/instances/{instance_id}/GetCustomer')
async def get_customer(
    instance_id: int,
    request: GetCustomerRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False, description="强制刷新")
):
    """查询账户"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetCustomer',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetAllCustomers')
async def get_all_customers(
    instance_id: int,
    request: GetAllCustomersRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """获取所有账户账号"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetAllCustomers',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetPayHistory')
async def get_pay_history(
    instance_id: int,
    request: GetPayHistoryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询缴费记录"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetPayHistory',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetConsumption')
async def get_consumption(
    instance_id: int,
    request: GetConsumptionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询其它收入记录"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetConsumption',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetCustomerPhoneBook')
async def get_customer_phone_book(
    instance_id: int,
    request: GetCustomerPhoneBookRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询账户电话簿"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetCustomerPhoneBook',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetPhone')
async def get_phone(
    instance_id: int,
    request: GetPhoneRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询话机"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetPhone',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetPhoneOnline')
async def get_phone_online(
    instance_id: int,
    request: GetPhoneOnlineRequest = Body(default=GetPhoneOnlineRequest()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询在线话机"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetPhoneOnline',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetAllPhoneOnline')
async def get_all_phone_online(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """获取所有在线话机"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetAllPhoneOnline',
        params={},
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetGatewayMapping')
async def get_gateway_mapping(
    instance_id: int,
    request: GetGatewayMappingRequest = Body(default=GetGatewayMappingRequest()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询对接网关"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetGatewayMapping',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetGatewayMappingOnline')
async def get_gateway_mapping_online(
    instance_id: int,
    request: GetGatewayMappingOnlineRequest = Body(default=GetGatewayMappingOnlineRequest()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询在线对接网关"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetGatewayMappingOnline',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetGatewayRouting')
async def get_gateway_routing(
    instance_id: int,
    request: GetGatewayRoutingRequest = Body(default=GetGatewayRoutingRequest()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询落地网关"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetGatewayRouting',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetGatewayRoutingOnline')
async def get_gateway_routing_online(
    instance_id: int,
    request: GetGatewayRoutingOnlineRequest = Body(default=GetGatewayRoutingOnlineRequest()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询在线落地网关"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetGatewayRoutingOnline',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetCurrentCall')
async def get_current_call(
    instance_id: int,
    request: GetCurrentCallRequest = Body(default=GetCurrentCallRequest()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询当前通话"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetCurrentCall',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetCdr')
async def get_cdr(
    instance_id: int,
    request: GetCdrRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询历史话单(CDR)"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetCdr',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetAvailableTime')
async def get_available_time(
    instance_id: int,
    request: GetAvailableTimeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """获取可用通话时长"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetAvailableTime',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetIvrSecondAvailableTime')
async def get_ivr_second_available_time(
    instance_id: int,
    request: GetIvrSecondAvailableTimeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """获取IVR第二路可用通话时长"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetIvrSecondAvailableTime',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetFeeRateGroup')
async def get_fee_rate_group(
    instance_id: int,
    request: GetFeeRateGroupRequest = Body(default=GetFeeRateGroupRequest()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询费率组"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetFeeRateGroup',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetFeeRate')
async def get_fee_rate(
    instance_id: int,
    request: GetFeeRateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询费率"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetFeeRate',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetSuite')
async def get_suite(
    instance_id: int,
    request: GetSuiteRequest = Body(default=GetSuiteRequest()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询套餐"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetSuite',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetSuiteOrder')
async def get_suite_order(
    instance_id: int,
    request: GetSuiteOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询套餐订单"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetSuiteOrder',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetCurrentSuite')
async def get_current_suite(
    instance_id: int,
    request: GetCurrentSuiteRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询生效套餐"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetCurrentSuite',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetActivePhoneCard')
async def get_active_phone_card(
    instance_id: int,
    request: GetActivePhoneCardRequest = Body(default=GetActivePhoneCardRequest()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询在用电话卡"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetActivePhoneCard',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetBindedE164')
async def get_binded_e164(
    instance_id: int,
    request: GetBindedE164Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询绑定号码"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetBindedE164',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetPhoneCard')
async def get_phone_card(
    instance_id: int,
    request: GetPhoneCardRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询电话卡"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetPhoneCard',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetReportCustomerFee')
async def get_report_customer_fee(
    instance_id: int,
    request: GetReportCustomerFeeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询账户明细报表"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetReportCustomerFee',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetReportPhoneFee')
async def get_report_phone_fee(
    instance_id: int,
    request: GetReportPhoneFeeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询话机明细报表"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetReportPhoneFee',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetReportCustomerLocationFee')
async def get_report_customer_location_fee(
    instance_id: int,
    request: GetReportCustomerLocationFeeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询账户地区明细报表"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetReportCustomerLocationFee',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetE164Convert')
async def get_e164_convert(
    instance_id: int,
    request: GetE164ConvertRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询号码变换表"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetE164Convert',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetSoftSwitch')
async def get_soft_switch(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询软交换"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetSoftSwitch',
        params={},
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetPerformance')
async def get_performance(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """查询性能"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetPerformance',
        params={},
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetAlarmCurrent')
async def get_alarm_current(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """获取当前告警"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetAlarmCurrent',
        params={},
        db=db,
        refresh=refresh
    )


@router.post('/instances/{instance_id}/GetIvrAudio')
async def get_ivr_audio(
    instance_id: int,
    request: GetIvrAudioRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    refresh: bool = Query(False)
):
    """获取IVR语音"""
    return await query_vos_api(
        instance_id=instance_id,
        api_path='/external/server/GetIvrAudio',
        params=request.dict(),
        db=db,
        refresh=refresh
    )


# ==================== 缓存管理接口 ====================

@router.delete('/instances/{instance_id}/cache')
async def clear_cache(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    api_path: Optional[str] = Query(None, description="API路径，不指定则清除所有缓存")
):
    """清除缓存"""
    cache_service = VosCacheService(db)
    cache_service.invalidate_cache(
        vos_instance_id=instance_id,
        api_path=api_path
    )
    
    return {
        'success': True,
        'message': f'缓存已清除 (instance_id={instance_id}, api_path={api_path or "all"})'
    }


@router.get('/instances/{instance_id}/cache/stats')
async def get_cache_stats(
    instance_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """获取缓存统计信息"""
    cache_service = VosCacheService(db)
    stats = cache_service.get_cache_stats(instance_id)
    
    return {
        'success': True,
        'instance_id': instance_id,
        'stats': stats
    }

