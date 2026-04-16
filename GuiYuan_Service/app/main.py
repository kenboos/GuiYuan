"""
归园服务端 - FastAPI 应用入口

技术栈: Python 3.11+ / FastAPI / SQLAlchemy(asyncio) / MySQL / Redis / Pydantic v2
"""
import datetime
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.config import settings
from app.db import init_db
from app.core.exceptions import AppException

logger = logging.getLogger("guiyuan")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    logger.info("正在连接数据库...")
    await init_db()
    logger.info("数据库连接成功")
    # 启动定时任务(开发模式)
    if settings.debug:
        from app.jobs.scheduler import start_scheduler
        start_scheduler()
        logger.info("定时任务已启动")
    yield


# 创建应用实例
app = FastAPI(
    title="归园 API",
    description="在线农场 x 线下实地 - 服务端接口",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://guiyuan.farm"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 全局异常处理 ==========

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.detail["code"], "message": exc.detail["message"], "data": None},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.debug:
        logger.error("[Error] %s %s: %s", request.method, request.url, exc)
    return JSONResponse(
        status_code=500,
        content={
            "code": 1002,
            "message": str(exc) if settings.debug else "服务器内部错误",
            "data": None,
        },
    )


# ========== 健康检查 ==========

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}


# ========== 注册路由模块 ==========
from app.api.v1.router import api_router  # noqa: E402
app.include_router(api_router)

logger.info("所有路由已注册")
