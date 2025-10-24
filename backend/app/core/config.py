import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL Database (配置数据)
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://vosadmin:Ykxx@2025@postgres:5432/vosadmin')
    
    # ClickHouse Database (话单数据)
    CLICKHOUSE_HOST: str = os.getenv('CLICKHOUSE_HOST', 'clickhouse')
    CLICKHOUSE_PORT: int = int(os.getenv('CLICKHOUSE_PORT', '9000'))
    CLICKHOUSE_HTTP_PORT: int = int(os.getenv('CLICKHOUSE_HTTP_PORT', '8123'))
    CLICKHOUSE_USER: str = os.getenv('CLICKHOUSE_USER', 'vosadmin')
    CLICKHOUSE_PASSWORD: str = os.getenv('CLICKHOUSE_PASSWORD', 'Ykxx@2025')
    CLICKHOUSE_DB: str = os.getenv('CLICKHOUSE_DB', 'vos_cdrs')
    
    # Redis
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    
    # JWT
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # App
    API_V1_PREFIX: str = '/api/v1'
    PROJECT_NAME: str = 'YK-VOS API'
    
    class Config:
        case_sensitive = True

settings = Settings()

