import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://vos:vos123@db:5432/vosdb')
    
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

