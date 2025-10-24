from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, vos, cdr, vos_api, sync_config, tasks, sync

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f'{settings.API_V1_PREFIX}/openapi.json',
    docs_url='/docs',
    redoc_url='/redoc'
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(vos.router, prefix=settings.API_V1_PREFIX)
app.include_router(cdr.router, prefix=settings.API_V1_PREFIX)
app.include_router(vos_api.router, prefix=settings.API_V1_PREFIX)
app.include_router(sync_config.router, prefix=settings.API_V1_PREFIX)
app.include_router(sync.router, prefix=f'{settings.API_V1_PREFIX}/sync', tags=['同步管理'])
app.include_router(tasks.router, prefix=settings.API_V1_PREFIX)

@app.get('/')
async def root():
    return {'message': 'YK-VOS API Server', 'status': 'running'}

@app.get('/health')
async def health():
    return {'status': 'ok'}

