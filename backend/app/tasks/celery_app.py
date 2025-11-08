from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery = Celery('vos_tasks', broker=settings.REDIS_URL, backend=settings.REDIS_URL)
# celery.conf.task_routes = {'app.tasks.sync_tasks.*': {'queue': 'sync'}}  # 暂时禁用队列路由，使用默认队列
celery.conf.timezone = 'Asia/Shanghai'
celery.conf.beat_schedule = {
    # 原有任务
    'sync-phones-every-5min': {'task': 'app.tasks.sync_tasks.sync_all_instances_online_phones','schedule': 300.0},
    'sync-cdr-daily-0130': {'task': 'app.tasks.sync_tasks.sync_all_instances_cdrs','schedule': crontab(minute=30, hour=1)},
    'sync-customers-every-10min': {'task': 'app.tasks.sync_tasks.sync_all_instances_customers','schedule': 600.0},
    
    # 通用VOS API数据同步任务
    'sync-all-vos-common-apis-every-1min': {
        'task': 'app.tasks.sync_tasks.sync_all_vos_common_apis',
        'schedule': 60.0,  # 每1分钟检查一次（根据各API的TTL自动决定是否同步）
    },
    
    # 增强版同步任务（专门表 + 通用缓存双写）
    'sync-all-instances-enhanced-every-4hours': {
        'task': 'app.tasks.sync_tasks.sync_all_instances_enhanced',
        'schedule': 14400.0,  # 每4小时同步一次（话机、网关、费率、套餐）
    },
    
    # 网关专用同步任务
    'sync-all-gateways-every-4hours': {
        'task': 'app.tasks.sync_tasks.sync_all_instances_gateways',
        'schedule': 14400.0,  # 每4小时同步一次网关（对接+落地）
    },
    
    # 清理过期缓存（每天凌晨2点）
    'cleanup-expired-cache-daily': {
        'task': 'app.tasks.sync_tasks.cleanup_expired_cache',
        'schedule': crontab(minute=0, hour=2),
    },
    
    # VOS实例健康检查（每5分钟）
    'check-vos-health-every-5min': {
        'task': 'app.tasks.sync_tasks.check_vos_instances_health',
        'schedule': 300.0,  # 每5分钟检查一次
    },
    
    # 话单费用统计（每天凌晨2点30分执行）
    'calculate-cdr-statistics-daily': {
        'task': 'app.tasks.cdr_statistics_tasks.calculate_all_instances_statistics',
        'schedule': crontab(minute=30, hour=2),  # 每天凌晨2点30分
    },
    
    # 每小时刷新仪表盘统计物化视图
    'refresh-dashboard-statistics': {
        'task': 'app.tasks.sync_tasks.refresh_dashboard_statistics_view',
        'schedule': crontab(minute=0),  # 每小时的第0分钟执行
    },
    
    # 账户明细报表同步（每天凌晨3点执行，在CDR统计之后）
    'sync-account-detail-reports-daily': {
        'task': 'app.tasks.account_detail_report_tasks.sync_account_detail_reports_daily',
        'schedule': crontab(minute=0, hour=3),  # 每天凌晨3点
    },
}

# 导入任务模块以注册任务
from app.tasks import sync_tasks  # noqa: E402, F401
from app.tasks import initial_sync_tasks  # noqa: E402, F401
from app.tasks import manual_sync_tasks  # noqa: E402, F401
from app.tasks import cdr_statistics_tasks  # noqa: E402, F401
from app.tasks import account_detail_report_tasks  # noqa: E402, F401
