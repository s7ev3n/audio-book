from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List

from ...services.audio_service import AudioService

router = APIRouter()
audio_service = AudioService()

@router.post("/merge/book")
async def merge_book_audio(book_id: str, chapter_ids: List[str]):
    """合并整本书的音频"""
    try:
        merged_audio_path = await audio_service.merge_book_audio(
            book_id=book_id,
            chapter_ids=chapter_ids
        )
        return {
            "status": "success",
            "merged_audio_url": f"/storage/audio/{merged_audio_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"合并音频失败: {str(e)}")

@router.get("/download/{audio_file}")
async def download_audio(audio_file: str):
    """下载音频文件"""
    try:
        file_path = audio_service.get_audio_file_path(audio_file)
        if not file_path:
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        return FileResponse(
            path=file_path,
            filename=audio_file,
            media_type='audio/mpeg'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")

@router.get("/books/{book_id}/playlist")
async def get_book_playlist(book_id: str):
    """获取书籍播放列表"""
    try:
        playlist = await audio_service.get_book_playlist(book_id)
        return {"playlist": playlist}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"获取播放列表失败: {str(e)}")