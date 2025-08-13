import asyncio
import uuid
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from concurrent.futures import ThreadPoolExecutor
import re
import json

from ..core.config import settings
from ..models.schemas import TranslationTask, TaskStatus
from .epub_service import EpubService

class TranslationService:
    def __init__(self):
        self.epub_service = EpubService()
        self.active_tasks: Dict[str, TranslationTask] = {}
        self.executor = ThreadPoolExecutor(max_workers=settings.max_workers)
    
    def _clean_html_content(self, html_content: str) -> str:
        """清理HTML内容，提取纯文本"""
        # 移除XML声明和DOCTYPE
        content = re.sub(r'<\?xml[^>]*\?>', '', html_content)
        content = re.sub(r'<!DOCTYPE[^>]*>', '', content)
        
        # 将段落标签替换为换行符，保持段落结构
        content = re.sub(r'</p>\s*<p[^>]*>', '\n\n', content)
        content = re.sub(r'<p[^>]*>', '', content)
        content = re.sub(r'</p>', '\n', content)
        
        # 移除其他HTML标签，但保留文本内容
        content = re.sub(r'<[^>]+>', '', content)
        
        # 清理多余的空白字符
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # 最多保留两个换行符
        content = re.sub(r'[ \t]+', ' ', content)  # 合并空格和制表符
        content = content.strip()
        
        return content
    
    def _convert_numbers_to_chinese(self, text: str) -> str:
        """将文本中的阿拉伯数字转换为中文数字"""
        def number_to_chinese(num_str):
            """将数字字符串转换为中文"""
            # 中文数字映射
            digit_map = {'0': '零', '1': '一', '2': '二', '3': '三', '4': '四', 
                        '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'}
            
            # 处理版本号格式 (如: 1.5.2, 3.14.159)
            if '.' in num_str and num_str.count('.') > 1:
                parts = num_str.split('.')
                chinese_parts = []
                for part in parts:
                    if part.isdigit():
                        chinese_parts.append(self._convert_integer_to_chinese(part, digit_map))
                    else:
                        chinese_parts.append(part)
                return '点'.join(chinese_parts)
            
            # 处理普通小数 (如: 2.1, 3.14)
            elif '.' in num_str:
                integer_part, decimal_part = num_str.split('.')
                chinese_integer = self._convert_integer_to_chinese(integer_part, digit_map)
                chinese_decimal = '点' + ''.join(digit_map[d] for d in decimal_part)
                return chinese_integer + chinese_decimal
            
            # 处理整数
            return self._convert_integer_to_chinese(num_str, digit_map)
        
        def replace_number(match):
            return number_to_chinese(match.group())
        
        # 匹配独立的数字（包括小数和版本号格式）
        pattern = r'\b\d+(?:\.\d+)*\b'
        return re.sub(pattern, replace_number, text)
    
    def _convert_integer_to_chinese(self, num_str: str, digit_map: dict) -> str:
        """将整数字符串转换为中文"""
        if not num_str or not num_str.isdigit():
            return num_str
            
        # 如果是4位年份，逐位转换
        if len(num_str) == 4:
            return ''.join(digit_map[d] for d in num_str)
        
        # 处理普通数字
        num = int(num_str)
        if num == 0:
            return '零'
        elif num < 10:
            return digit_map[str(num)]
        elif num < 100:
            tens = num // 10
            ones = num % 10
            if ones == 0:
                return digit_map[str(tens)] + '十'
            elif tens == 1:
                return '十' + digit_map[str(ones)]
            else:
                return digit_map[str(tens)] + '十' + digit_map[str(ones)]
        elif num < 1000:
            hundreds = num // 100
            remainder = num % 100
            result = digit_map[str(hundreds)] + '百'
            if remainder == 0:
                return result
            elif remainder < 10:
                return result + '零' + digit_map[str(remainder)]
            else:
                tens = remainder // 10
                ones = remainder % 10
                if tens == 0:
                    return result + '零' + digit_map[str(ones)]
                elif ones == 0:
                    return result + digit_map[str(tens)] + '十'
                else:
                    return result + digit_map[str(tens)] + '十' + digit_map[str(ones)]
        else:
            # 对于更大的数字，简单逐位转换
            return ''.join(digit_map[d] for d in num_str)
    
    def _init_ai_clients(self):
        """初始化AI客户端"""
        self.siliconflow_client = None
        
        # 硅基流动 API 配置
        if hasattr(settings, 'siliconflow_api_key') and settings.siliconflow_api_key:
            self.siliconflow_api_key = settings.siliconflow_api_key
            self.siliconflow_base_url = getattr(settings, 'siliconflow_base_url', 'https://api.siliconflow.cn/v1')
            
            # 创建 HTTP 客户端，基础配置
            self.siliconflow_client = httpx.AsyncClient(
                base_url=self.siliconflow_base_url,
                timeout=httpx.Timeout(60.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
            
            print(f"硅基流动客户端初始化成功，API 地址: {self.siliconflow_base_url}")
        else:
            raise ValueError("未配置硅基流动 API 密钥，请在环境变量中设置 SILICONFLOW_API_KEY 或在配置中设置 siliconflow_api_key")
    
    async def translate(self, text: str, source_lang: str = "en", 
                       target_lang: str = "zh", model: str = None) -> str:
        """翻译单个文本片段"""
        if not model:
            model = getattr(settings, 'translation_model', 'Qwen/Qwen2.5-7B-Instruct')
        
        if not self.siliconflow_client:
            raise ValueError("硅基流动客户端未初始化")
        
        try:
            return await self._translate_with_siliconflow(text, source_lang, target_lang, model)
        except Exception as e:
            print(f"翻译API调用失败 - 错误详情: {str(e)}")
            raise Exception(f"翻译失败: {str(e)}")
    
    async def _translate_with_siliconflow(self, text: str, source_lang: str, 
                                        target_lang: str, model: str) -> str:
        """使用硅基流动进行翻译，包含重试机制"""
        prompt = self._build_translation_prompt(text, source_lang, target_lang)
        
        # 重试配置
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 按照硅基流动 API 格式构建请求
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000,
                    "stream": False
                }
                
                print(f"发送翻译请求到: {self.siliconflow_base_url}/chat/completions (尝试 {retry_count + 1}/{max_retries})")
                print(f"使用模型: {model}")
                print(f"文本长度: {len(text)} 字符")
                
                # 使用完整的 URL 路径发送请求，增加超时时间
                response = await self.siliconflow_client.post(
                    "/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.siliconflow_api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=120.0  # 增加超时时间到120秒
                )
                
                print(f"API响应状态码: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"API错误响应: {error_text}")
                    
                    # 服务器错误可以重试
                    if response.status_code >= 500:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"服务器错误，等待5秒后重试...")
                            await asyncio.sleep(5)
                            continue
                    
                    raise Exception(f"硅基流动 API 请求失败: {response.status_code} - {error_text}")
                
                result = response.json()
                print(f"API响应成功，获得翻译结果")
                
                # 检查响应格式
                if "choices" not in result or not result["choices"]:
                    raise Exception(f"API响应格式错误: {result}")
                
                choice = result["choices"][0]
                if "message" not in choice or "content" not in choice["message"]:
                    raise Exception(f"API响应消息格式错误: {choice}")
                
                translated_text = choice["message"]["content"].strip()
                
                if not translated_text:
                    raise Exception("翻译结果为空")
                
                # 对翻译结果进行数字转换处理（针对中文翻译）
                if target_lang == "zh":
                    translated_text = self._convert_numbers_to_chinese(translated_text)
                
                return translated_text
                
            except httpx.RequestError as e:
                retry_count += 1
                print(f"网络请求错误详情 (尝试 {retry_count}/{max_retries}): {type(e).__name__}: {str(e)}")
                
                # 网络超时错误可以重试
                if retry_count < max_retries and ("timeout" in str(e).lower() or "readtimeout" in str(e).lower()):
                    print(f"网络超时，等待10秒后重试...")
                    await asyncio.sleep(10)
                    continue
                
                # 用完重试次数或不可重试的错误
                if retry_count >= max_retries:
                    raise Exception(f"网络请求失败，已重试{max_retries}次: {str(e)}")
                else:
                    raise Exception(f"网络请求失败: {str(e)}")
            
            except Exception as e:
                # 其他错误通常不可重试
                print(f"翻译处理错误: {str(e)}")
                raise Exception(f"翻译处理失败: {str(e)}")
        
        raise Exception(f"翻译请求失败，已达到最大重试次数: {max_retries}")
    
    def _build_translation_prompt(self, text: str, source_lang: str, target_lang: str) -> str:
        """构建翻译提示词"""
        lang_map = {
            "en": "英文",
            "zh": "中文"
        }
        
        source_name = lang_map.get(source_lang, source_lang)
        target_name = lang_map.get(target_lang, target_lang)
        
        return f"""你是一个专业的文学翻译专家，请将以下{source_name}文本翻译成流畅自然的{target_name}。

原文：
{text}

翻译要求：
1. 保持原文的文学风格和语调
2. 确保翻译流畅自然，符合中文表达习惯
3. 保留原文的段落格式和结构
4. 对于专有名词，请保持前后一致性
5. **重要：所有阿拉伯数字必须转换为中文数字，以便语音合成时正确读音**
   - 整数：1→一，2→二，10→十，25→二十五，100→一百
   - 小数：2.1→二点一，3.14→三点一四
   - 版本号：1.5.2→一点五点二，Chapter 2.1→第二点一章
   - 年份：1995→一九九五年，2024→二零二四年
6. 年份数字逐位转换，普通数字按中文习惯转换
7. 只返回翻译结果，不要包含解释、评论或其他内容

请开始翻译："""
    
    async def translate_chapter(self, book_id: str, chapter_id: str, 
                              model: str = None) -> str:
        """翻译整个章节"""
        task_id = str(uuid.uuid4())
        
        # 创建翻译任务
        task = TranslationTask(
            id=task_id,
            book_id=book_id,
            chapter_id=chapter_id,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.active_tasks[task_id] = task
        print(f"创建翻译任务: {task_id} for book: {book_id}, chapter: {chapter_id}")
        
        # 异步执行翻译
        asyncio.create_task(self._process_chapter_translation(
            task_id, book_id, chapter_id, model
        ))
        
        return task_id
    
    async def _process_chapter_translation(self, task_id: str, book_id: str, 
                                         chapter_id: str, model: str = None):
        """处理章节翻译任务"""
        print(f"开始处理翻译任务: {task_id}")
        
        if task_id not in self.active_tasks:
            print(f"任务 {task_id} 不存在于 active_tasks 中")
            return
            
        task = self.active_tasks[task_id]
        
        try:
            # 更新任务状态
            task.status = TaskStatus.IN_PROGRESS
            print(f"任务 {task_id} 状态更新为 IN_PROGRESS")
            
            # 获取章节内容
            content = self.epub_service.get_chapter_content(book_id, chapter_id)
            print(f"任务 {task_id} 获取到章节内容，长度: {len(content)}")
            
            # 清理HTML标签，提取纯文本用于翻译
            clean_content = self._clean_html_content(content)
            print(f"任务 {task_id} 清理HTML后内容长度: {len(clean_content)}")
            
            # 将长文本分块处理
            chunks = self._split_text_into_chunks(clean_content)
            total_chunks = len(chunks)
            print(f"任务 {task_id} 分割成 {total_chunks} 个块")
            
            translated_chunks = []
            
            for i, chunk in enumerate(chunks):
                print(f"任务 {task_id} 翻译第 {i+1}/{total_chunks} 块")
                # 翻译当前块
                translated_chunk = await self.translate(
                    chunk, "en", "zh", model
                )
                translated_chunks.append(translated_chunk)
                print(f"任务 {task_id} 第 {i+1} 块翻译完成")
                
                # 更新进度
                task.progress = (i + 1) / total_chunks
                
                # 添加延迟避免API限流
                await asyncio.sleep(0.5)
            
            # 合并翻译结果
            full_translation = "\n\n".join(translated_chunks)
            print(f"任务 {task_id} 翻译完成，总长度: {len(full_translation)}")
            
            # 保存翻译结果
            translation_path = await self._save_translation(
                book_id, chapter_id, full_translation
            )
            print(f"任务 {task_id} 翻译结果已保存到: {translation_path}")
            
            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.progress = 1.0
            task.completed_at = datetime.now()
            print(f"任务 {task_id} 状态更新为 COMPLETED")
            
        except Exception as e:
            print(f"任务 {task_id} 执行失败: {str(e)}")
            if hasattr(e, '__cause__') and e.__cause__:
                print(f"异常详情: {type(e.__cause__).__name__}: {str(e.__cause__)}")
            
            # 确保任务仍在active_tasks中
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.now()
                print(f"任务 {task_id} 状态更新为 FAILED，错误信息: {str(e)}")
            else:
                print(f"警告：任务 {task_id} 在异常处理时不在 active_tasks 中")
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = None) -> List[str]:
        """将长文本分割成适合翻译的块"""
        if not chunk_size:
            chunk_size = getattr(settings, 'chunk_size', 1000)
        
        print(f"开始分割文本，总长度: {len(text)}，块大小限制: {chunk_size}")
        
        # 按段落分割
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # 如果单个段落就超过了限制，需要进一步分割
            if len(paragraph) > chunk_size:
                # 先保存当前块（如果有的话）
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # 按句子分割过长的段落
                sentences = self._split_paragraph_by_sentences(paragraph, chunk_size)
                chunks.extend(sentences)
                
            elif len(current_chunk) + len(paragraph) + 2 > chunk_size and current_chunk:
                # 当前块加上新段落会超过限制，先保存当前块
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                # 添加到当前块
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        print(f"文本分割完成，共 {len(chunks)} 个块，长度分别为: {[len(chunk) for chunk in chunks]}")
        return chunks
    
    def _split_paragraph_by_sentences(self, paragraph: str, chunk_size: int) -> List[str]:
        """将过长的段落按句子分割"""
        sentences = re.split(r'[.!?]+\s+', paragraph)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 如果单个句子就超过限制，只能强制分割
            if len(sentence) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # 强制按字符数分割
                for i in range(0, len(sentence), chunk_size):
                    chunks.append(sentence[i:i+chunk_size])
                    
            elif len(current_chunk) + len(sentence) + 1 > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    async def _save_translation(self, book_id: str, chapter_id: str, 
                              translation: str) -> str:
        """保存翻译结果"""
        # 创建翻译文件目录
        translation_dir = os.path.join(getattr(settings, 'translation_dir', './storage/translations'), book_id)
        os.makedirs(translation_dir, exist_ok=True)
        
        # 将章节ID转换为安全的文件名（替换斜杠为下划线）
        safe_chapter_id = chapter_id.replace('/', '_').replace('\\', '_')
        
        # 保存翻译文件
        file_path = os.path.join(translation_dir, f"{safe_chapter_id}.txt")
        print(f"保存翻译结果到: {file_path}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(translation)
        
        return file_path
    
    def get_translation_status(self, task_id: str) -> Dict[str, Any]:
        """获取翻译任务状态"""
        print(f"查询翻译任务状态: {task_id}")
        print(f"当前活跃任务列表: {list(self.active_tasks.keys())}")
        
        if task_id not in self.active_tasks:
            raise Exception(f"找不到翻译任务: {task_id}")
        
        task = self.active_tasks[task_id]
        
        return {
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message
        }
    
    async def get_translation_result(self, book_id: str, chapter_id: str) -> Optional[str]:
        """获取翻译结果"""
        # 将章节ID转换为安全的文件名（与保存时保持一致）
        safe_chapter_id = chapter_id.replace('/', '_').replace('\\', '_')
        
        translation_path = os.path.join(
            getattr(settings, 'translation_dir', './storage/translations'), 
            book_id, 
            f"{safe_chapter_id}.txt"
        )
        
        print(f"尝试加载翻译文件: {translation_path}")
        
        if os.path.exists(translation_path):
            print(f"找到翻译文件，正在读取...")
            with open(translation_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"翻译内容长度: {len(content)} 字符")
                return content
        else:
            print(f"翻译文件不存在: {translation_path}")
        
        return None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口，关闭客户端连接"""
        if self.siliconflow_client:
            await self.siliconflow_client.aclose()
