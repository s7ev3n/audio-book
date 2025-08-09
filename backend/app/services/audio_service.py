import os
import asyncio
from typing import List, Dict, Any, Optional
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime

from ..core.config import settings
from ..models.schemas import PlaylistItem, BookPlaylist
from .epub_service import EpubService
from .tts_service import TTSService

class AudioService:
    def __init__(self):
        self.epub_service = EpubService()
        self.tts_service = TTSService()
        self.executor = ThreadPoolExecutor(max_workers=settings.max_workers)
    
    async def merge_book_audio(self, book_id: str, chapter_ids: List[str]) -> str:
        """合并整本书的音频"""
        try:
            # 收集所有章节音频文件
            audio_files = []
            total_duration = 0.0
            
            for chapter_id in chapter_ids:
                audio_info = await self.tts_service.get_chapter_audio_info(
                    book_id, chapter_id
                )
                
                if not audio_info:
                    raise Exception(f"章节 {chapter_id} 的音频文件不存在")
                
                # 构建音频文件路径
                audio_filename = f"{book_id}_{chapter_id}.mp3"
                audio_path = os.path.join(settings.audio_dir, audio_filename)
                
                if os.path.exists(audio_path):
                    audio_files.append(audio_path)
                    total_duration += audio_info["duration"]
                else:
                    raise Exception(f"音频文件不存在: {audio_path}")
            
            # 执行音频合并
            merged_filename = f"{book_id}_complete.mp3"
            merged_path = await self._merge_multiple_audio_files(
                audio_files, merged_filename
            )
            
            # 保存播放列表元数据
            await self._save_book_metadata(
                book_id, chapter_ids, total_duration, merged_filename
            )
            
            return os.path.basename(merged_path)
            
        except Exception as e:
            raise Exception(f"合并音频失败: {str(e)}")
    
    async def _merge_multiple_audio_files(self, audio_files: List[str], 
                                        output_filename: str) -> str:
        """合并多个音频文件"""
        def _merge():
            if not audio_files:
                raise Exception("没有音频文件可合并")
            
            # 加载第一个音频文件
            merged_audio = AudioSegment.from_mp3(audio_files[0])
            
            # 依次合并其他音频文件
            for audio_file in audio_files[1:]:
                # 添加章节间隔（2秒静音）
                silence = AudioSegment.silent(duration=2000)
                next_audio = AudioSegment.from_mp3(audio_file)
                merged_audio = merged_audio + silence + next_audio
            
            # 保存合并后的音频
            output_path = os.path.join(settings.audio_dir, output_filename)
            
            # 导出为高质量MP3
            merged_audio.export(
                output_path,
                format="mp3",
                bitrate="192k",
                tags={
                    "title": "Complete Audiobook",
                    "artist": "Audio Book Translator",
                    "genre": "Audiobook"
                }
            )
            
            return output_path
        
        # 在线程池中执行
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, _merge
        )
    
    async def _save_book_metadata(self, book_id: str, chapter_ids: List[str], 
                                total_duration: float, merged_filename: str):
        """保存书籍音频元数据"""
        metadata = {
            "book_id": book_id,
            "chapter_ids": chapter_ids,
            "total_duration": total_duration,
            "merged_filename": merged_filename,
            "created_at": datetime.now().isoformat(),
            "chapter_count": len(chapter_ids)
        }
        
        # 保存元数据文件
        metadata_path = os.path.join(settings.audio_dir, f"{book_id}_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def get_audio_file_path(self, audio_file: str) -> Optional[str]:
        """获取音频文件的完整路径"""
        audio_path = os.path.join(settings.audio_dir, audio_file)
        
        if os.path.exists(audio_path) and os.path.isfile(audio_path):
            return audio_path
        
        return None
    
    async def get_book_playlist(self, book_id: str) -> BookPlaylist:
        """获取书籍的播放列表"""
        try:
            # 获取书籍信息
            chapters = self.epub_service.get_chapters(book_id)
            
            # 构建播放列表项
            playlist_items = []
            total_duration = 0.0
            
            for chapter in chapters:
                # 检查章节音频是否存在
                audio_info = await self.tts_service.get_chapter_audio_info(
                    book_id, chapter.id
                )
                
                if audio_info:
                    item = PlaylistItem(
                        chapter_id=chapter.id,
                        chapter_title=chapter.title,
                        audio_url=audio_info["audio_url"],
                        duration=audio_info["duration"],
                        order=chapter.order
                    )
                    playlist_items.append(item)
                    total_duration += audio_info["duration"]
            
            # 按章节顺序排序
            playlist_items.sort(key=lambda x: x.order)
            
            # 获取书籍标题（假设从chapters中可以推断）
            book_title = f"Book {book_id}"  # 这里可以从数据库或缓存获取实际标题
            
            return BookPlaylist(
                book_id=book_id,
                book_title=book_title,
                total_duration=total_duration,
                items=playlist_items
            )
            
        except Exception as e:
            raise Exception(f"获取播放列表失败: {str(e)}")
    
    async def create_chapter_segments(self, book_id: str, chapter_id: str, 
                                    segment_duration: int = 300) -> List[Dict[str, Any]]:
        """将章节音频分割成指定时长的片段（用于渐进式加载）"""
        try:
            # 获取章节音频文件
            audio_filename = f"{book_id}_{chapter_id}.mp3"
            audio_path = os.path.join(settings.audio_dir, audio_filename)
            
            if not os.path.exists(audio_path):
                raise Exception(f"章节音频文件不存在: {audio_filename}")
            
            def _create_segments():
                # 加载音频文件
                audio = AudioSegment.from_mp3(audio_path)
                audio_duration = len(audio)  # 毫秒
                segment_duration_ms = segment_duration * 1000  # 转换为毫秒
                
                segments = []
                segment_count = 0
                
                # 分割音频
                for start_time in range(0, audio_duration, segment_duration_ms):
                    end_time = min(start_time + segment_duration_ms, audio_duration)
                    segment = audio[start_time:end_time]
                    
                    # 保存片段
                    segment_filename = f"{book_id}_{chapter_id}_seg_{segment_count:03d}.mp3"
                    segment_path = os.path.join(settings.audio_dir, segment_filename)
                    
                    segment.export(segment_path, format="mp3", bitrate="128k")
                    
                    segments.append({
                        "segment_id": segment_count,
                        "filename": segment_filename,
                        "start_time": start_time / 1000.0,  # 转换为秒
                        "end_time": end_time / 1000.0,
                        "duration": (end_time - start_time) / 1000.0,
                        "url": f"/storage/audio/{segment_filename}"
                    })
                    
                    segment_count += 1
                
                return segments
            
            # 在线程池中执行
            segments = await asyncio.get_event_loop().run_in_executor(
                self.executor, _create_segments
            )
            
            return segments
            
        except Exception as e:
            raise Exception(f"创建音频片段失败: {str(e)}")
    
    async def cleanup_audio_files(self, book_id: str, chapter_ids: List[str] = None):
        """清理音频文件"""
        try:
            files_to_remove = []
            
            if chapter_ids:
                # 清理指定章节的音频文件
                for chapter_id in chapter_ids:
                    audio_filename = f"{book_id}_{chapter_id}.mp3"
                    audio_path = os.path.join(settings.audio_dir, audio_filename)
                    if os.path.exists(audio_path):
                        files_to_remove.append(audio_path)
            else:
                # 清理整本书的所有音频文件
                audio_dir = settings.audio_dir
                for filename in os.listdir(audio_dir):
                    if filename.startswith(f"{book_id}_"):
                        file_path = os.path.join(audio_dir, filename)
                        if os.path.isfile(file_path):
                            files_to_remove.append(file_path)
            
            # 删除文件
            for file_path in files_to_remove:
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # 忽略删除失败的文件
            
            return {"deleted_files": len(files_to_remove)}
            
        except Exception as e:
            raise Exception(f"清理音频文件失败: {str(e)}")
    
    async def get_audio_statistics(self, book_id: str) -> Dict[str, Any]:
        """获取音频文件统计信息"""
        try:
            audio_dir = settings.audio_dir
            stats = {
                "book_id": book_id,
                "chapter_count": 0,
                "total_size": 0,
                "total_duration": 0.0,
                "files": []
            }
            
            # 扫描音频文件
            for filename in os.listdir(audio_dir):
                if filename.startswith(f"{book_id}_") and filename.endswith(".mp3"):
                    file_path = os.path.join(audio_dir, filename)
                    file_size = os.path.getsize(file_path)
                    
                    # 获取音频时长
                    try:
                        audio = AudioSegment.from_mp3(file_path)
                        duration = len(audio) / 1000.0  # 转换为秒
                    except:
                        duration = 0.0
                    
                    file_info = {
                        "filename": filename,
                        "size": file_size,
                        "duration": duration,
                        "url": f"/storage/audio/{filename}"
                    }
                    
                    stats["files"].append(file_info)
                    stats["total_size"] += file_size
                    stats["total_duration"] += duration
                    
                    if not filename.endswith("_complete.mp3"):
                        stats["chapter_count"] += 1
            
            return stats
            
        except Exception as e:
            raise Exception(f"获取音频统计失败: {str(e)}")