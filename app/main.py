import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import router as api_router
from .config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="TCP连接监控系统", version="1.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "message": "TCP连接监控系统API",
        "endpoints": [
            "/api/tcp/stats - 获取所有代理服务器TCP统计数据",
            "/api/tcp/stats/{proxy_server} - 获取特定代理服务器统计数据",
            "/api/tcp/connections - 获取所有TCP连接详情"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"启动服务器: {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.RELOAD
    )