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

@router.get("/books", response_model=List[BookInfo])
async def get_books():
    """获取所有已上传的书籍列表"""
    try:
        books = epub_service.get_all_books()
        return books
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取书籍列表失败: {str(e)}")

@router.get("/books/{book_id}", response_model=BookInfo)
async def get_book(book_id: str):
    """获取单个书籍信息"""
    try:
        book = epub_service.get_book_info(book_id)
        return book
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"获取书籍信息失败: {str(e)}")

@router.delete("/books/{book_id}")
async def delete_book(book_id: str):
    """删除书籍"""
    print(f"API: 收到删除书籍请求 - book_id: {book_id}")
    try:
        epub_service.delete_book(book_id)
        print(f"API: 书籍删除成功 - book_id: {book_id}")
        return {"message": "书籍删除成功", "book_id": book_id}
    except Exception as e:
        print(f"API: 删除书籍失败 - book_id: {book_id}, error: {str(e)}")
        raise HTTPException(status_code=404, detail=f"删除书籍失败: {str(e)}")

@router.get("/books/{book_id}/chapters", response_model=List[ChapterInfo])
async def get_chapters(book_id: str):
    """获取书籍章节列表"""
    try:
        chapters = epub_service.get_chapters(book_id)
        return chapters
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"获取章节失败: {str(e)}")

@router.get("/books/{book_id}/chapters/{chapter_id:path}")
async def get_chapter_content(book_id: str, chapter_id: str):
    """获取章节内容"""
    try:
        print(f"API接收到请求 - book_id: {book_id}, chapter_id: {chapter_id}")
        
        # URL解码章节ID
        from urllib.parse import unquote
        decoded_chapter_id = unquote(chapter_id)
        print(f"解码后的章节ID: {decoded_chapter_id}")
        
        content = epub_service.get_chapter_content(book_id, decoded_chapter_id)
        return {"content": content}
    except Exception as e:
        print(f"获取章节内容出错: {str(e)}")
        raise HTTPException(status_code=404, detail=f"获取章节内容失败: {str(e)}")