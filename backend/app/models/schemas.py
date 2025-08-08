from pydantic import BaseModel
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
    id: str
    title: str
    content_length: int
    order: int

class BookInfo(BaseModel):
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
    text: str
    model: Optional[str] = "gpt-3.5-turbo"
    context: Optional[str] = None

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    model_used: Optional[str] = None

class TranslationTask(BaseModel):
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
    text: str
    voice: Optional[str] = "zh-CN-XiaoxiaoNeural"
    speed: Optional[float] = 1.0
    pitch: Optional[str] = "default"

class TTSResponse(BaseModel):
    audio_url: str
    text: str
    voice: str
    duration: Optional[float] = None

class AudioTask(BaseModel):
    id: str
    book_id: str
    chapter_id: str
    translation_id: str
    status: TaskStatus
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

# 音频合并相关
class PlaylistItem(BaseModel):
    chapter_id: str
    chapter_title: str
    audio_url: str
    duration: float
    order: int

class BookPlaylist(BaseModel):
    book_id: str
    book_title: str
    total_duration: float
    items: List[PlaylistItem]