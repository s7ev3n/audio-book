import os
import sys
import uuid
import tempfile
import asyncio
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# 添加F5-TTS到Python路径
sys.path.append("/workspace/F5-TTS/src")

from f5_tts.api import F5TTS

app = FastAPI(title="F5-TTS Service", version="1.0.0")

# 全局变量
tts_model = None
executor = ThreadPoolExecutor(max_workers=4)
active_tasks = {}

class TTSRequest(BaseModel):
    text: str
    language: str = "auto"  # "zh", "en", or "auto"
    speed: float = 1.0
    remove_silence: bool = True
    ref_audio_url: Optional[str] = None  # 可选的参考音频URL或路径
    ref_text: Optional[str] = None  # 可选的参考文本

class TTSResponse(BaseModel):
    task_id: str
    status: str
    message: str = ""

class TaskStatus(BaseModel):
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: float = 0.0
    audio_url: Optional[str] = None
    error_message: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """初始化F5-TTS模型"""
    global tts_model
    try:
        print("Initializing F5-TTS model...")
        tts_model = F5TTS(
            model="F5TTS_v1_Base",
            device=None  # 自动检测设备
        )
        print("F5-TTS model initialized successfully")
    except Exception as e:
        print(f"Failed to initialize F5-TTS model: {e}")
        print("Service will start without TTS model loaded")
        # 不抛出异常，让服务继续启动
        tts_model = None

def detect_language(text: str) -> str:
    """检测文本语言"""
    # 简单的中文检测：如果包含中文字符则为中文
    has_chinese = any(ord(char) > 127 for char in text)
    return "zh" if has_chinese else "en"

def get_reference_audio(language: str, custom_ref_audio: Optional[str] = None, custom_ref_text: Optional[str] = None):
    """获取参考音频和文本"""
    # 如果提供了自定义参考音频，使用自定义的
    if custom_ref_audio and custom_ref_text is not None:
        return custom_ref_audio, custom_ref_text
    
    # 使用自定义的默认参考音频（风头圈音频），文本置空
    # 不论什么语言都使用同一个自定义音频，因为F5-TTS主要学习音色特征
    ref_audio = "/workspace/ref_audio/fengtouquan.wav"
    ref_text = ""  # 置空避免在生成音频前包含参考文本
    
    return ref_audio, ref_text

def synthesize_audio(task_id: str, text: str, language: str, speed: float, remove_silence: bool, 
                    ref_audio_url: Optional[str] = None, ref_text_custom: Optional[str] = None):
    """执行TTS合成"""
    try:
        # 更新任务状态
        active_tasks[task_id]["status"] = "processing"
        active_tasks[task_id]["progress"] = 0.1
        
        # 检测语言
        if language == "auto":
            language = detect_language(text)
        
        # 获取参考音频（可能是自定义的）
        ref_audio, ref_text = get_reference_audio(language, ref_audio_url, ref_text_custom)
        
        # 创建输出文件
        output_dir = "/tmp/f5tts_outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{task_id}.wav")
        
        active_tasks[task_id]["progress"] = 0.3
        
        # 执行TTS推理
        wav, sr, spec = tts_model.infer(
            ref_file=ref_audio,
            ref_text=ref_text,
            gen_text=text,
            speed=speed,
            file_wave=output_file,
            remove_silence=remove_silence
        )
        
        # 任务完成
        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["progress"] = 1.0
        active_tasks[task_id]["audio_url"] = f"/audio/{task_id}.wav"
        
    except Exception as e:
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["error_message"] = str(e)
        print(f"TTS synthesis failed for task {task_id}: {e}")

@app.post("/tts", response_model=TTSResponse)
async def create_tts_task(request: TTSRequest, background_tasks: BackgroundTasks):
    """创建TTS任务"""
    if not tts_model:
        raise HTTPException(status_code=503, detail="TTS model not initialized - model download failed")
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    active_tasks[task_id] = {
        "status": "pending",
        "progress": 0.0,
        "audio_url": None,
        "error_message": None
    }
    
    # 添加后台任务
    background_tasks.add_task(
        synthesize_audio,
        task_id=task_id,
        text=request.text,
        language=request.language,
        speed=request.speed,
        remove_silence=request.remove_silence,
        ref_audio_url=request.ref_audio_url,
        ref_text_custom=request.ref_text
    )
    
    return TTSResponse(
        task_id=task_id,
        status="pending",
        message="Task created successfully"
    )

@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = active_tasks[task_id]
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        audio_url=task["audio_url"],
        error_message=task["error_message"]
    )

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """下载音频文件"""
    file_path = f"/tmp/f5tts_outputs/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        file_path,
        media_type="audio/wav",
        filename=filename
    )

@app.post("/upload-ref-audio")
async def upload_reference_audio(file: UploadFile = File(...)):
    """上传参考音频文件"""
    # 检查文件类型
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # 创建上传目录
    upload_dir = "/tmp/f5tts_ref_audio"
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1] if file.filename else '.wav'
    file_path = os.path.join(upload_dir, f"{file_id}{file_extension}")
    
    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "file_id": file_id,
            "file_path": file_path,
            "filename": file.filename,
            "message": "Reference audio uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "model_loaded": tts_model is not None,
        "active_tasks": len(active_tasks)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)