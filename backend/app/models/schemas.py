from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

# EPUB 相关模型
class ChapterInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    id: str
    title: str
    content_length: int
    order: int

class BookInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    id: str
    title: str
    author: Optional[str] = None
    language: str = "en"
    total_chapters: int
    chapters: List[ChapterInfo]
    upload_time: datetime
    file_path: str

# 翻译相关模型
class TranslationRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    text: str
    model: Optional[str] = "gpt-3.5-turbo"
    context: Optional[str] = None

class TranslationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    translation_model: Optional[str] = None

class TranslationTask(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    id: str
    book_id: str
    chapter_id: str
    status: TaskStatus
    progress: float = 0.0
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

# TTS 相关模型
class TTSRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    text: str
    voice: Optional[str] = "zh-CN-XiaoxiaoNeural"
    speed: Optional[float] = 1.0
    pitch: Optional[str] = "default"
    ref_audio_url: Optional[str] = None  # 可选的参考音频URL
    ref_text: Optional[str] = None  # 可选的参考文本

class TTSResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    audio_url: str
    text: str
    voice: str
    duration: Optional[float] = None

class AudioTask(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    id: str
    book_id: str
    chapter_id: str
    translation_id: Optional[str] = None
    status: TaskStatus
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    progress: Optional[float] = 0.0
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

# 音频合并相关
class PlaylistItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    chapter_id: str
    chapter_title: str
    audio_url: str
    duration: float
    order: int

class BookPlaylist(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    book_id: str
    book_title: str
    total_duration: float
    items: List[PlaylistItem]