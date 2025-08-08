from fastapi import APIRouter

# 导入各个模块的路由
from .endpoints import epub, translation, tts, audio

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(epub.router, prefix="/epub", tags=["epub"])
api_router.include_router(translation.router, prefix="/translation", tags=["translation"])
api_router.include_router(tts.router, prefix="/tts", tags=["tts"])
api_router.include_router(audio.router, prefix="/audio", tags=["audio"])