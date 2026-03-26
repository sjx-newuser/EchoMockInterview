"""
Echo Mock System - FastAPI ASGI 应用入口
=========================================
职责：挂载路由、CORS 中间件、全局异常处理器。
不包含任何业务逻辑。
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth, interview, report, ws

app = FastAPI(
    title="Echo Mock System API",
    description="AI 驱动的沉浸式模拟面试平台",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# =============================================
# CORS 跨域中间件
# =============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 开发阶段全放通；生产环境请收窄为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================
# 路由挂载
# =============================================
app.include_router(auth.router,      prefix="/api/v1")
app.include_router(interview.router, prefix="/api/v1")
app.include_router(report.router,    prefix="/api/v1")
app.include_router(ws.router,        prefix="/api/v1")


# =============================================
# 全局异常处理器
# =============================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """将 Pydantic 参数校验失败统一封装为可读的 JSON 响应。"""
    return JSONResponse(
        status_code=400,
        content={
            "code": 40001,
            "message": "请求参数校验失败",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """兜底：捕获未处理的异常，防止泄露堆栈信息。"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 50000,
            "message": "服务器内部错误，请稍后重试",
        },
    )


# =============================================
# 健康检查
# =============================================

@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "ok"}
