import asyncio
import uuid
import os
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment
import tempfile
import httpx

from ..core.config import settings
from ..models.schemas import AudioTask, TaskStatus
from .translation_service import TranslationService

class TTSService:
    def __init__(self):
        self.translation_service = TranslationService()
        self.active_tasks: Dict[str, AudioTask] = {}
        self.executor = ThreadPoolExecutor(max_workers=settings.max_workers)
        
        # 初始化TTS客户端
        self._init_tts_clients()
    
    def _init_tts_clients(self):
        """初始化TTS客户端"""
        self.azure_speech_config = None
        self.f5tts_service_url = getattr(settings, 'f5tts_service_url', 'http://f5tts-service:8001')
        
        # 初始化Azure TTS（如果配置了）
        if settings.azure_tts_key and settings.azure_tts_region:
            self.azure_speech_config = speechsdk.SpeechConfig(
                subscription=settings.azure_tts_key,
                region=settings.azure_tts_region
            )
            self.azure_speech_config.speech_synthesis_voice_name = settings.tts_voice
    
    async def text_to_speech(self, text: str, voice: str = None, 
                            speed: float = 1.0, ref_audio_url: Optional[str] = None,
                            ref_text: Optional[str] = None) -> Dict[str, Any]:
        """将文本转换为语音"""
        if not voice:
            voice = settings.tts_voice
        
        # 生成唯一的音频文件名
        audio_id = str(uuid.uuid4())
        audio_filename = f"{audio_id}.wav"
        audio_path = os.path.join(settings.audio_dir, audio_filename)
        
        # 确保音频目录存在
        os.makedirs(settings.audio_dir, exist_ok=True)
        
        try:
            if settings.tts_provider == "f5tts":
                await self._synthesize_with_f5tts_service(
                    text, audio_path, speed, ref_audio_url, ref_text
                )
            elif self.azure_speech_config:
                await self._synthesize_with_azure(
                    text, audio_path, voice, speed
                )
            else:
                raise Exception("未配置任何TTS服务")
            
            # 获取音频时长
            duration = self._get_audio_duration(audio_path)
            
            return {
                "audio_id": audio_id,
                "audio_path": audio_path,
                "audio_filename": audio_filename,
                "duration": duration
            }
            
        except Exception as e:
            # 清理失败的文件
            if os.path.exists(audio_path):
                os.remove(audio_path)
            raise Exception(f"TTS合成失败: {str(e)}")
    
    async def _synthesize_with_azure(self, text: str, output_path: str, 
                                   voice: str, speed: float):
        """使用Azure TTS合成语音"""
        # 创建音频配置
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
        
        # 设置语音
        speech_config = self.azure_speech_config
        speech_config.speech_synthesis_voice_name = voice
        
        # 创建合成器
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # 构建SSML以控制语速
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
            <voice name="{voice}">
                <prosody rate="{speed}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        # 执行合成
        def _synthesize():
            result = synthesizer.speak_ssml(ssml)
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return True
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                raise Exception(f"语音合成被取消: {cancellation_details.reason}")
            else:
                raise Exception("语音合成失败")
        
        # 在线程池中执行
        await asyncio.get_event_loop().run_in_executor(
            self.executor, _synthesize
        )
    
    async def _synthesize_with_f5tts_service(self, text: str, output_path: str, speed: float, 
                                           ref_audio_url: Optional[str] = None, ref_text: Optional[str] = None):
        """使用F5-TTS微服务合成语音"""
        async with httpx.AsyncClient(timeout=300.0) as client:
            # 创建TTS任务请求
            tts_request = {
                "text": text,
                "language": "auto",
                "speed": speed,
                "remove_silence": True
            }
            
            # 如果提供了自定义参考音频，添加到请求中
            if ref_audio_url:
                tts_request["ref_audio_url"] = ref_audio_url
            if ref_text is not None:
                tts_request["ref_text"] = ref_text
            
            # 创建TTS任务
            response = await client.post(
                f"{self.f5tts_service_url}/tts",
                json=tts_request
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to create TTS task: {response.text}")
            
            task_data = response.json()
            task_id = task_data["task_id"]
            
            # 轮询任务状态
            while True:
                status_response = await client.get(
                    f"{self.f5tts_service_url}/task/{task_id}"
                )
                
                if status_response.status_code != 200:
                    raise Exception(f"Failed to get task status: {status_response.text}")
                
                status_data = status_response.json()
                
                if status_data["status"] == "completed":
                    # 下载音频文件
                    audio_filename = status_data["audio_url"].split("/")[-1]
                    audio_response = await client.get(
                        f"{self.f5tts_service_url}/audio/{audio_filename}"
                    )
                    
                    if audio_response.status_code != 200:
                        raise Exception(f"Failed to download audio: {audio_response.text}")
                    
                    # 保存音频文件
                    with open(output_path, "wb") as f:
                        f.write(audio_response.content)
                    break
                    
                elif status_data["status"] == "failed":
                    raise Exception(f"TTS synthesis failed: {status_data.get('error_message', 'Unknown error')}")
                
                # 等待一段时间后重新检查
                await asyncio.sleep(2)
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频文件时长（秒）"""
        try:
            if audio_path.endswith('.mp3'):
                audio = AudioSegment.from_mp3(audio_path)
            else:
                audio = AudioSegment.from_wav(audio_path)
            return len(audio) / 1000.0  # 转换为秒
        except Exception:
            return 0.0
    
    async def generate_chapter_audio(self, book_id: str, chapter_id: str, 
                                   translation_id: Optional[str] = None) -> str:
        """为章节生成音频"""
        task_id = str(uuid.uuid4())
        
        # 如果没有提供translation_id，尝试从已存在的翻译中获取
        if not translation_id:
            # 获取翻译内容，不需要特定的translation_id
            try:
                translation_content = await self.translation_service.get_translation_result(book_id, chapter_id)
                if not translation_content:
                    raise ValueError("未找到章节翻译内容，请先翻译章节")
            except Exception as e:
                raise ValueError(f"获取翻译内容失败: {str(e)}")
        
        # 创建音频任务
        task = AudioTask(
            id=task_id,
            book_id=book_id,
            chapter_id=chapter_id,
            translation_id=translation_id,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.active_tasks[task_id] = task
        
        # 异步执行音频生成
        asyncio.create_task(self._process_chapter_audio_generation(
            task_id, book_id, chapter_id, translation_id
        ))
        
        return task_id
    
    async def _process_chapter_audio_generation(self, task_id: str, book_id: str, 
                                              chapter_id: str, translation_id: Optional[str] = None):
        """处理章节音频生成任务"""
        task = self.active_tasks[task_id]
        
        try:
            # 更新任务状态
            task.status = TaskStatus.IN_PROGRESS
            
            # 获取翻译内容
            translation_content = await self.translation_service.get_translation_result(
                book_id, chapter_id
            )
            
            if not translation_content:
                raise Exception(f"找不到章节 {chapter_id} 的翻译内容")
            
            # 翻译内容现在已经是清理后的纯文本
            if not translation_content.strip():
                raise Exception(f"章节 {chapter_id} 的翻译内容为空")
            
            print(f"翻译内容长度: {len(translation_content)}")
            print(f"翻译内容预览: {translation_content[:200]}...")
            
            # 将长文本分段处理，避免TTS限制
            segments = self._split_text_for_tts(translation_content)
            audio_segments = []
            
            for i, segment in enumerate(segments):
                # 生成单个段落的音频，使用自定义参考音频
                segment_result = await self.text_to_speech(
                    segment, 
                    ref_audio_url="/workspace/ref_audio/fengtouquan.wav",
                    ref_text=""
                )
                audio_segments.append(segment_result["audio_path"])
                
                # 更新进度
                task.progress = (i + 1) / len(segments) * 0.8  # 80%用于生成，20%用于合并
            
            # 合并音频段落
            merged_audio_path = await self._merge_audio_segments(
                audio_segments, book_id, chapter_id
            )
            
            # 清理临时文件
            for segment_path in audio_segments:
                if os.path.exists(segment_path):
                    os.remove(segment_path)
            
            # 获取最终音频时长
            duration = self._get_audio_duration(merged_audio_path)
            
            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.progress = 1.0
            task.audio_url = f"/storage/audio/{os.path.basename(merged_audio_path)}"
            task.duration = duration
            task.completed_at = datetime.now()
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
    
    def _split_text_for_tts(self, text: str, max_length: int = 1000) -> List[str]:
        """将文本分割为适合TTS的段落"""
        # 按句子分割
        sentences = text.split('。')
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 如果当前段落加上新句子超过限制
            if len(current_segment) + len(sentence) > max_length and current_segment:
                segments.append(current_segment + '。')
                current_segment = sentence
            else:
                if current_segment:
                    current_segment += '。' + sentence
                else:
                    current_segment = sentence
        
        # 添加最后一个段落
        if current_segment:
            segments.append(current_segment + '。')
        
        return segments
    
    async def _merge_audio_segments(self, segment_paths: List[str], 
                                  book_id: str, chapter_id: str) -> str:
        """合并多个音频段落"""
        def _merge():
            # 加载第一个音频
            merged_audio = AudioSegment.from_wav(segment_paths[0])
            
            # 依次合并其他音频
            for segment_path in segment_paths[1:]:
                segment_audio = AudioSegment.from_wav(segment_path)
                # 添加0.5秒的间隔
                silence = AudioSegment.silent(duration=500)
                merged_audio = merged_audio + silence + segment_audio
            
            # 保存合并后的音频
            # 将chapter_id中的斜杠和其他特殊字符替换为安全字符
            safe_chapter_id = chapter_id.replace("/", "_").replace("\\", "_").replace(":", "_")
            output_filename = f"{book_id}_{safe_chapter_id}.mp3"
            output_path = os.path.join(settings.audio_dir, output_filename)
            
            # 转换为MP3格式以减小文件大小
            merged_audio.export(output_path, format="mp3", bitrate="128k")
            
            return output_path
        
        # 在线程池中执行
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, _merge
        )
    
    def get_audio_status(self, task_id: str) -> Dict[str, Any]:
        """获取音频生成任务状态"""
        if task_id not in self.active_tasks:
            raise Exception(f"找不到音频任务: {task_id}")
        
        task = self.active_tasks[task_id]
        
        return {
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "audio_url": task.audio_url,
            "duration": task.duration,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message
        }
    
    async def get_chapter_audio_info(self, book_id: str, chapter_id: str) -> Optional[Dict[str, Any]]:
        """获取章节音频信息"""
        # 使用与生成时相同的文件名转换逻辑
        safe_chapter_id = chapter_id.replace("/", "_").replace("\\", "_").replace(":", "_")
        audio_filename = f"{book_id}_{safe_chapter_id}.mp3"
        audio_path = os.path.join(settings.audio_dir, audio_filename)
        
        if os.path.exists(audio_path):
            duration = self._get_audio_duration(audio_path)
            return {
                "audio_url": f"/storage/audio/{audio_filename}",
                "duration": duration,
                "file_size": os.path.getsize(audio_path)
            }
        
        return None