from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ...services.translation_service import TranslationService
from ...models.schemas import TranslationRequest, TranslationResponse

router = APIRouter()
translation_service = TranslationService()

@router.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """翻译文本"""
    try:
        result = await translation_service.translate(
            text=request.text,
            source_lang="en",
            target_lang="zh",
            model=request.model
        )
        return TranslationResponse(
            original_text=request.text,
            translated_text=result,
            source_lang="en",
            target_lang="zh"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")

@router.post("/translate/chapter")
async def translate_chapter(book_id: str, chapter_id: str):
    """翻译整个章节"""
    try:
        result = await translation_service.translate_chapter(book_id, chapter_id)
        return {"status": "success", "translation_id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译章节失败: {str(e)}")

@router.get("/translation/{translation_id}")
async def get_translation_status(translation_id: str):
    """获取翻译进度"""
    try:
        status = translation_service.get_translation_status(translation_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"获取翻译状态失败: {str(e)}")

@router.get("/books/{book_id}/chapters/{chapter_id:path}/translation")
async def get_chapter_translation(book_id: str, chapter_id: str):
    """获取章节翻译结果"""
    try:
        translation = await translation_service.get_translation_result(book_id, chapter_id)
        if translation:
            return {"translation": translation}
        else:
            raise HTTPException(status_code=404, detail="翻译结果不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取翻译结果失败: {str(e)}")

@router.post("/translate/chapter/retranslate")
async def retranslate_chapter(book_id: str, chapter_id: str, force: bool = False):
    """重新翻译指定章节"""
    try:
        task_id = await translation_service.retranslate_chapter(book_id, chapter_id, force)
        return {"status": "success", "translation_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新翻译失败: {str(e)}")

@router.get("/tasks/summary")
async def get_tasks_summary():
    """获取所有活跃翻译任务的摘要"""
    try:
        summary = translation_service.get_active_tasks_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务摘要失败: {str(e)}")

@router.post("/tasks/cleanup")
async def cleanup_tasks(max_age_hours: int = 24):
    """清理已完成的翻译任务"""
    try:
        cleaned_count = translation_service.cleanup_completed_tasks(max_age_hours)
        return {"status": "success", "cleaned_tasks": cleaned_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理任务失败: {str(e)}")