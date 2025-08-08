from fastapi import APIRouter, HTTPException
from ...services.tts_service import TTSService
from ...models.schemas import TTSRequest, TTSResponse

router = APIRouter()
tts_service = TTSService()

@router.post("/generate", response_model=TTSResponse)
async def generate_speech(request: TTSRequest):
    """生成语音"""
    try:
        audio_result = await tts_service.text_to_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed
        )
        return TTSResponse(
            audio_url=f"/storage/audio/{audio_result['audio_filename']}",
            text=request.text,
            voice=request.voice or "zh-CN-XiaoxiaoNeural",
            duration=audio_result.get('duration')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS生成失败: {str(e)}")

@router.post("/generate/chapter")
async def generate_chapter_audio(book_id: str, chapter_id: str, translation_id: str):
    """为章节生成语音"""
    try:
        audio_id = await tts_service.generate_chapter_audio(
            book_id=book_id,
            chapter_id=chapter_id,
            translation_id=translation_id
        )
        return {"status": "success", "audio_id": audio_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成章节语音失败: {str(e)}")

@router.get("/audio/{audio_id}/status")
async def get_audio_generation_status(audio_id: str):
    """获取语音生成状态"""
    try:
        status = tts_service.get_audio_status(audio_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"获取语音状态失败: {str(e)}")

@router.get("/books/{book_id}/chapters/{chapter_id}/audio")
async def get_chapter_audio_info(book_id: str, chapter_id: str):
    """获取章节音频信息"""
    try:
        audio_info = await tts_service.get_chapter_audio_info(book_id, chapter_id)
        return audio_info or {"message": "章节音频不存在"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取章节音频信息失败: {str(e)}")