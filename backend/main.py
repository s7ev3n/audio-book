from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.core.config import settings
from app.api import api_router

# 创建 FastAPI 实例
app = FastAPI(
    title="Audio Book Translator API",
    description="Convert English EPUB to Chinese Audiobooks",
    version="1.0.0"
)

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# 路由配置
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Audio Book Translator API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )