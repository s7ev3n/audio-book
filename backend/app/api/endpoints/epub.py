from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List
import os
import uuid

from ...core.config import settings
from ...services.epub_service import EpubService
from ...models.schemas import BookInfo, ChapterInfo

router = APIRouter()
epub_service = EpubService()

@router.post("/upload", response_model=BookInfo)
async def upload_epub(file: UploadFile = File(...)):
    """上传EPUB文件"""
    if not file.filename.endswith('.epub'):
        raise HTTPException(status_code=400, detail="只支持EPUB文件")
    
    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.upload_dir, f"{file_id}.epub")
    
    # 保存文件
    os.makedirs(settings.upload_dir, exist_ok=True)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # 解析EPUB
    try:
        book_info = epub_service.parse_epub(file_path, file_id)
        return book_info
    except Exception as e:
        # 清理上传的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"EPUB解析失败: {str(e)}")

@router.get("/books/{book_id}/chapters", response_model=List[ChapterInfo])
async def get_chapters(book_id: str):
    """获取书籍章节列表"""
    try:
        chapters = epub_service.get_chapters(book_id)
        return chapters
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"获取章节失败: {str(e)}")

@router.get("/books/{book_id}/chapters/{chapter_id}")
async def get_chapter_content(book_id: str, chapter_id: str):
    """获取章节内容"""
    try:
        content = epub_service.get_chapter_content(book_id, chapter_id)
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"获取章节内容失败: {str(e)}")