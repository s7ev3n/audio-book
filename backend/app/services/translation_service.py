import asyncio
import uuid
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import openai
import anthropic
from concurrent.futures import ThreadPoolExecutor
import re

from ..core.config import settings
from ..models.schemas import TranslationTask, TaskStatus
from .epub_service import EpubService

class TranslationService:
    def __init__(self):
        self.epub_service = EpubService()
        self.active_tasks: Dict[str, TranslationTask] = {}
        self.executor = ThreadPoolExecutor(max_workers=settings.max_workers)
        
        # 初始化AI客户端
        self._init_ai_clients()
    
    def _init_ai_clients(self):
        """初始化AI客户端"""
        self.openai_client = None
        self.claude_client = None
        
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.openai_client = openai
        
        if settings.claude_api_key:
            self.claude_client = anthropic.Anthropic(api_key=settings.claude_api_key)
    
    async def translate(self, text: str, source_lang: str = "en", 
                       target_lang: str = "zh", model: str = None) -> str:
        """翻译单个文本片段"""
        if not model:
            model = settings.translation_model
        
        try:
            if model.startswith("gpt-") and self.openai_client:
                return await self._translate_with_openai(text, source_lang, target_lang, model)
            elif model.startswith("claude-") and self.claude_client:
                return await self._translate_with_claude(text, source_lang, target_lang, model)
            else:
                raise ValueError(f"不支持的翻译模型: {model}")
        
        except Exception as e:
            raise Exception(f"翻译失败: {str(e)}")
    
    async def _translate_with_openai(self, text: str, source_lang: str, 
                                   target_lang: str, model: str) -> str:
        """使用OpenAI进行翻译"""
        prompt = self._build_translation_prompt(text, source_lang, target_lang)
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的文学翻译家，擅长将英文小说翻译成流畅自然的中文。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )\n            )\n            \n            return response.choices[0].message.content.strip()\n            \n        except Exception as e:\n            raise Exception(f\"OpenAI翻译失败: {str(e)}\")\n    \n    async def _translate_with_claude(self, text: str, source_lang: str, \n                                   target_lang: str, model: str) -> str:\n        \"\"\"使用Claude进行翻译\"\"\"\n        prompt = self._build_translation_prompt(text, source_lang, target_lang)\n        \n        try:\n            response = await asyncio.get_event_loop().run_in_executor(\n                self.executor,\n                lambda: self.claude_client.messages.create(\n                    model=model,\n                    max_tokens=4000,\n                    messages=[\n                        {\"role\": \"user\", \"content\": prompt}\n                    ]\n                )\n            )\n            \n            return response.content[0].text.strip()\n            \n        except Exception as e:\n            raise Exception(f\"Claude翻译失败: {str(e)}\")\n    \n    def _build_translation_prompt(self, text: str, source_lang: str, target_lang: str) -> str:\n        \"\"\"构建翻译提示词\"\"\"\n        lang_map = {\n            \"en\": \"英文\",\n            \"zh\": \"中文\"\n        }\n        \n        source_name = lang_map.get(source_lang, source_lang)\n        target_name = lang_map.get(target_lang, target_lang)\n        \n        return f\"\"\"请将以下{source_name}文本翻译成流畅自然的{target_name}：\n\n原文：\n{text}\n\n要求：\n1. 保持原文的文学风格和语调\n2. 确保翻译流畅自然，符合中文表达习惯\n3. 保留段落格式\n4. 对于专有名词，请保持一致性\n5. 只返回翻译结果，不要包含其他内容\n\n翻译：\"\"\"\n    \n    async def translate_chapter(self, book_id: str, chapter_id: str, \n                              model: str = None) -> str:\n        \"\"\"翻译整个章节\"\"\"\n        task_id = str(uuid.uuid4())\n        \n        # 创建翻译任务\n        task = TranslationTask(\n            id=task_id,\n            book_id=book_id,\n            chapter_id=chapter_id,\n            status=TaskStatus.PENDING,\n            created_at=datetime.now()\n        )\n        \n        self.active_tasks[task_id] = task\n        \n        # 异步执行翻译\n        asyncio.create_task(self._process_chapter_translation(\n            task_id, book_id, chapter_id, model\n        ))\n        \n        return task_id\n    \n    async def _process_chapter_translation(self, task_id: str, book_id: str, \n                                         chapter_id: str, model: str = None):\n        \"\"\"处理章节翻译任务\"\"\"\n        task = self.active_tasks[task_id]\n        \n        try:\n            # 更新任务状态\n            task.status = TaskStatus.IN_PROGRESS\n            \n            # 获取章节内容\n            content = self.epub_service.get_chapter_content(book_id, chapter_id)\n            \n            # 将长文本分块处理\n            chunks = self._split_text_into_chunks(content)\n            total_chunks = len(chunks)\n            \n            translated_chunks = []\n            \n            for i, chunk in enumerate(chunks):\n                # 翻译当前块\n                translated_chunk = await self.translate(\n                    chunk, \"en\", \"zh\", model\n                )\n                translated_chunks.append(translated_chunk)\n                \n                # 更新进度\n                task.progress = (i + 1) / total_chunks\n            \n            # 合并翻译结果\n            full_translation = \"\\n\\n\".join(translated_chunks)\n            \n            # 保存翻译结果\n            translation_path = await self._save_translation(\n                book_id, chapter_id, full_translation\n            )\n            \n            # 更新任务状态\n            task.status = TaskStatus.COMPLETED\n            task.progress = 1.0\n            task.completed_at = datetime.now()\n            \n        except Exception as e:\n            task.status = TaskStatus.FAILED\n            task.error_message = str(e)\n    \n    def _split_text_into_chunks(self, text: str, chunk_size: int = None) -> List[str]:\n        \"\"\"将长文本分割成适合翻译的块\"\"\"\n        if not chunk_size:\n            chunk_size = settings.chunk_size\n        \n        # 按段落分割\n        paragraphs = text.split('\\n\\n')\n        chunks = []\n        current_chunk = \"\"\n        \n        for paragraph in paragraphs:\n            # 如果当前块加上新段落超过限制，先保存当前块\n            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:\n                chunks.append(current_chunk.strip())\n                current_chunk = paragraph\n            else:\n                if current_chunk:\n                    current_chunk += \"\\n\\n\" + paragraph\n                else:\n                    current_chunk = paragraph\n        \n        # 添加最后一个块\n        if current_chunk:\n            chunks.append(current_chunk.strip())\n        \n        return chunks\n    \n    async def _save_translation(self, book_id: str, chapter_id: str, \n                              translation: str) -> str:\n        \"\"\"保存翻译结果\"\"\"\n        import os\n        \n        # 创建翻译文件目录\n        translation_dir = os.path.join(settings.translation_dir, book_id)\n        os.makedirs(translation_dir, exist_ok=True)\n        \n        # 保存翻译文件\n        file_path = os.path.join(translation_dir, f\"{chapter_id}.txt\")\n        \n        with open(file_path, 'w', encoding='utf-8') as f:\n            f.write(translation)\n        \n        return file_path\n    \n    def get_translation_status(self, task_id: str) -> Dict[str, Any]:\n        \"\"\"获取翻译任务状态\"\"\"\n        if task_id not in self.active_tasks:\n            raise Exception(f\"找不到翻译任务: {task_id}\")\n        \n        task = self.active_tasks[task_id]\n        \n        return {\n            \"task_id\": task.id,\n            \"status\": task.status,\n            \"progress\": task.progress,\n            \"created_at\": task.created_at.isoformat(),\n            \"completed_at\": task.completed_at.isoformat() if task.completed_at else None,\n            \"error_message\": task.error_message\n        }\n    \n    async def get_translation_result(self, book_id: str, chapter_id: str) -> Optional[str]:\n        \"\"\"获取翻译结果\"\"\"\n        translation_path = os.path.join(\n            settings.translation_dir, book_id, f\"{chapter_id}.txt\"\n        )\n        \n        if os.path.exists(translation_path):\n            with open(translation_path, 'r', encoding='utf-8') as f:\n                return f.read()\n        \n        return None