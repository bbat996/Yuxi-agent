import uvicorn

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from server.routers import router
from server.utils.auth_middleware import is_public_path
from server.src.utils.logging_config import logger


app = FastAPI()
app.include_router(router, prefix="/api")

# CORS 设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 鉴权中间件
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 获取请求路径
        path = request.url.path

        # 检查是否为公开路径，公开路径无需身份验证
        if is_public_path(path):
            return await call_next(request)

        if not path.startswith("/api"):
            # 非API路径，可能是前端路由或静态资源
            return await call_next(request)

        # 对于需要认证的API路径，让路由级别的认证处理
        # 这里不进行全局认证检查，而是让每个路由自己处理认证
        return await call_next(request)

# 添加鉴权中间件
app.add_middleware(AuthMiddleware)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5050, reload=True, workers=1)

