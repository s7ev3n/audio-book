from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=()  # 禁用保护命名空间警告
    )
    
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
    
    # 硅基流动配置
    siliconflow_api_key: Optional[str] = None
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    
    # 翻译模型配置
    translation_model: str = "deepseek-ai/DeepSeek-V3"  # 硅基流动推荐模型
    translation_provider: str = "siliconflow"  # 默认使用硅基流动
    
    # TTS 配置
    tts_provider: str = "f5tts"  # "azure" 或 "f5tts"
    azure_tts_key: Optional[str] = None
    azure_tts_region: Optional[str] = None
    tts_voice: str = "zh-CN-XiaoxiaoNeural"  # 中文语音
    
    # F5-TTS微服务配置
    f5tts_service_url: str = "http://localhost:8001"
    
    # 文件存储配置
    upload_dir: str = "./storage/uploads"
    translation_dir: str = "./storage/translations"
    audio_dir: str = "./storage/audio"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    
    # 并发配置
    max_workers: int = 4
    chunk_size: int = 1000  # 每次处理的字符数

# 创建全局设置实例
settings = Settings()