import os
import uuid
from typing import List, Dict, Optional
from datetime import datetime
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re

from ..core.config import settings
from ..models.schemas import BookInfo, ChapterInfo

class EpubService:
    def __init__(self):
        self.storage_path = settings.upload_dir
        self.parsed_books: Dict[str, epub.EpubBook] = {}
    
    def parse_epub(self, file_path: str, book_id: str) -> BookInfo:
        """解析EPUB文件并提取元数据和章节信息"""
        try:
            # 读取EPUB文件
            book = epub.read_epub(file_path)
            self.parsed_books[book_id] = book
            
            # 提取基本信息
            title = self._get_metadata(book, 'DC', 'title') or "Unknown Title"
            author = self._get_metadata(book, 'DC', 'creator') or "Unknown Author"
            language = self._get_metadata(book, 'DC', 'language') or "en"
            
            # 提取章节信息
            chapters = self._extract_chapters(book, book_id)
            
            # 创建书籍信息对象
            book_info = BookInfo(
                id=book_id,
                title=title,
                author=author,
                language=language,
                total_chapters=len(chapters),
                chapters=chapters,
                upload_time=datetime.now(),
                file_path=file_path
            )
            
            # 保存书籍信息到存储（这里可以扩展为数据库存储）
            self._save_book_info(book_info)
            
            return book_info
            
        except Exception as e:
            raise Exception(f"EPUB解析失败: {str(e)}")
    
    def _get_metadata(self, book: epub.EpubBook, namespace: str, name: str) -> Optional[str]:
        """提取EPUB元数据"""
        try:
            metadata = book.get_metadata(namespace, name)
            if metadata:
                return metadata[0][0] if isinstance(metadata[0], tuple) else str(metadata[0])
        except:
            pass
        return None
    
    def _extract_chapters(self, book: epub.EpubBook, book_id: str) -> List[ChapterInfo]:
        """提取章节信息"""
        chapters = []
        chapter_order = 0
        
        # 获取导航结构
        nav_items = list(book.get_items_of_type(ebooklib.ITEM_NAVIGATION))
        if nav_items:
            # 使用导航结构提取章节
            toc = book.toc
            chapters = self._extract_from_toc(toc, chapter_order, book_id)
        else:
            # 备用方法：从HTML文档提取
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content().decode('utf-8')
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # 尝试从标题提取章节名
                    title = self._extract_chapter_title(soup, item.get_name())
                    
                    if content.strip():  # 只有非空内容才算章节
                        chapters.append(ChapterInfo(
                            id=item.get_id() or f"chapter_{chapter_order}",
                            title=title,
                            content_length=len(self._clean_html_content(content)),
                            order=chapter_order
                        ))
                        chapter_order += 1
        
        return chapters
    
    def _extract_from_toc(self, toc, start_order: int = 0, book_id: str = None) -> List[ChapterInfo]:
        """从目录结构提取章节"""
        chapters = []
        order = start_order
        
        def process_toc_item(item):
            nonlocal order
            if isinstance(item, tuple) and len(item) >= 2:
                # (section, title, children)
                section = item[0]
                title = item[1] if isinstance(item[1], str) else str(item[1])
                
                if hasattr(section, 'href'):
                    # 获取内容长度
                    content = self.get_chapter_content_by_href(section.href, book_id)
                    chapters.append(ChapterInfo(
                        id=section.href.split('#')[0],  # 移除锚点
                        title=title,
                        content_length=len(content),
                        order=order
                    ))
                    order += 1
                
                # 处理子章节
                if len(item) > 2 and isinstance(item[2], list):
                    for child in item[2]:
                        process_toc_item(child)
            elif hasattr(item, 'href'):
                # 直接的链接项
                title = getattr(item, 'title', f"Chapter {order + 1}")
                content = self.get_chapter_content_by_href(item.href, book_id)
                chapters.append(ChapterInfo(
                    id=item.href.split('#')[0],
                    title=title,
                    content_length=len(content),
                    order=order
                ))
                order += 1
        
        for item in toc:
            process_toc_item(item)
        
        return chapters
    
    def _extract_chapter_title(self, soup: BeautifulSoup, default_name: str) -> str:
        """从HTML内容提取章节标题"""
        # 尝试从各种标题标签获取标题
        for tag in ['h1', 'h2', 'h3', 'title']:
            title_elem = soup.find(tag)
            if title_elem and title_elem.get_text().strip():
                return title_elem.get_text().strip()
        
        # 如果没有找到标题，使用文件名
        return default_name.replace('.xhtml', '').replace('.html', '').replace('_', ' ').title()
    
    def _clean_html_content(self, html_content: str) -> str:
        """清理HTML内容，提取纯文本"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 获取文本内容
        text = soup.get_text()
        
        # 清理空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def get_chapters(self, book_id: str) -> List[ChapterInfo]:
        """获取书籍的章节列表"""
        book_info = self._load_book_info(book_id)
        if not book_info:
            raise Exception(f"找不到书籍: {book_id}")
        
        return book_info.chapters
    
    def get_chapter_content(self, book_id: str, chapter_id: str) -> str:
        """获取章节的原始内容"""
        if book_id not in self.parsed_books:
            # 重新加载书籍
            book_info = self._load_book_info(book_id)
            if not book_info:
                raise Exception(f"找不到书籍: {book_id}")
            
            book = epub.read_epub(book_info.file_path)
            self.parsed_books[book_id] = book
        
        book = self.parsed_books[book_id]
        
        # 查找对应的章节
        for item in book.get_items():
            if item.get_id() == chapter_id or item.get_name() == chapter_id:
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content().decode('utf-8')
                    return self._clean_html_content(content)
        
        raise Exception(f"找不到章节: {chapter_id}")
    
    def get_chapter_content_by_href(self, href: str, book_id: str = None) -> str:
        """通过href获取章节内容（用于TOC解析）"""
        if book_id and book_id in self.parsed_books:
            book = self.parsed_books[book_id]
            # 移除锚点部分
            href_clean = href.split('#')[0]
            
            for item in book.get_items():
                if item.get_name() == href_clean or item.get_id() == href_clean:
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        content = item.get_content().decode('utf-8')
                        return self._clean_html_content(content)
        
        return ""
    
    def _save_book_info(self, book_info: BookInfo):
        """保存书籍信息（使用JSON文件存储）"""
        import json
        
        # 创建存储目录
        storage_dir = os.path.join(settings.upload_dir, "book_info")
        os.makedirs(storage_dir, exist_ok=True)
        
        # 保存书籍信息到JSON文件
        info_file = os.path.join(storage_dir, f"{book_info.id}.json")
        
        # 转换为可序列化的格式
        book_data = {
            "id": book_info.id,
            "title": book_info.title,
            "author": book_info.author,
            "language": book_info.language,
            "total_chapters": book_info.total_chapters,
            "upload_time": book_info.upload_time.isoformat(),
            "file_path": book_info.file_path,
            "chapters": [
                {
                    "id": ch.id,
                    "title": ch.title,
                    "content_length": ch.content_length,
                    "order": ch.order
                }
                for ch in book_info.chapters
            ]
        }
        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(book_data, f, ensure_ascii=False, indent=2)
    
    def _load_book_info(self, book_id: str) -> Optional[BookInfo]:
        """加载书籍信息（从JSON文件读取）"""
        import json
        
        storage_dir = os.path.join(settings.upload_dir, "book_info")
        info_file = os.path.join(storage_dir, f"{book_id}.json")
        
        if not os.path.exists(info_file):
            return None
        
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
            
            # 重建章节信息
            chapters = [
                ChapterInfo(
                    id=ch["id"],
                    title=ch["title"],
                    content_length=ch["content_length"],
                    order=ch["order"]
                )
                for ch in book_data["chapters"]
            ]
            
            # 重建书籍信息
            book_info = BookInfo(
                id=book_data["id"],
                title=book_data["title"],
                author=book_data.get("author"),
                language=book_data["language"],
                total_chapters=book_data["total_chapters"],
                chapters=chapters,
                upload_time=datetime.fromisoformat(book_data["upload_time"]),
                file_path=book_data["file_path"]
            )
            
            return book_info
            
        except Exception as e:
            print(f"Failed to load book info for {book_id}: {e}")
            return None