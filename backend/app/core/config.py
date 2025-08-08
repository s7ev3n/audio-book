from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # 基本配置
    project_name: str = "Audio Book Translator"
    version: str = "1.0.0"
    debug: bool = False
    
    # API 配置
    api_v1_str: str = "/api/v1"
    
    # 数据库配置
    database_url: str = "sqlite:///./audiobook.db"
    
    # AI 翻译配置
    openai_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    translation_model: str = "gpt-3.5-turbo"  # 或 claude-3-haiku
    
    # TTS 配置
    azure_tts_key: Optional[str] = None
    azure_tts_region: Optional[str] = None
    tts_voice: str = "zh-CN-XiaoxiaoNeural"  # 中文语音
    
    # 文件存储配置
    upload_dir: str = "./storage/uploads"
    translation_dir: str = "./storage/translations"
    audio_dir: str = "./storage/audio"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    
    # 并发配置
    max_workers: int = 4
    chunk_size: int = 1000  # 每次处理的字符数
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 创建全局设置实例
settings = Settings()