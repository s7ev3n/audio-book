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
        
        try:
            # 首先尝试从spine获取章节顺序（这是最可靠的方法）
            spine_items = []
            print(f"书籍spine信息: {book.spine}")
            for item_id, linear in book.spine:
                item = book.get_item_with_id(item_id)
                if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                    spine_items.append(item)
            
            print(f"从spine找到 {len(spine_items)} 个有效文档项")
            if spine_items:
                for item in spine_items:
                    try:
                        content = item.get_content().decode('utf-8')
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # 过滤掉非内容章节
                        if not self._is_content_chapter(item, soup, content):
                            continue
                        
                        # 提取章节标题
                        title = self._extract_chapter_title(soup, item.get_name())
                        
                        if content.strip():  # 只有非空内容才算章节
                            # 使用Name作为ID，因为这是章节内容检索时使用的
                            chapter_id = item.get_name() or item.get_id() or f"chapter_{chapter_order}"
                            chapters.append(ChapterInfo(
                                id=chapter_id,
                                title=title,
                                content_length=len(self._clean_html_content(content)),
                                order=chapter_order
                            ))
                            chapter_order += 1
                            print(f"添加spine章节: {title} (ID: {chapter_id})")
                    except Exception as e:
                        print(f"处理spine项目时出错: {e}")
                        continue
            else:
                # 获取导航结构
                try:
                    nav_items = list(book.get_items_of_type(ebooklib.ITEM_NAVIGATION))
                    if nav_items:
                        # 使用导航结构提取章节
                        toc = book.toc
                        chapters = self._extract_from_toc(toc, chapter_order, book_id)
                    else:
                        # 备用方法：从HTML文档提取
                        for item in book.get_items():
                            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                                try:
                                    content = item.get_content().decode('utf-8')
                                    soup = BeautifulSoup(content, 'html.parser')
                                    
                                    # 尝试从标题提取章节名
                                    title = self._extract_chapter_title(soup, item.get_name())
                                    
                                    if content.strip():  # 只有非空内容才算章节
                                        # 使用Name作为ID，因为这是章节内容检索时使用的
                                        chapter_id = item.get_name() or item.get_id() or f"chapter_{chapter_order}"
                                        chapters.append(ChapterInfo(
                                            id=chapter_id,
                                            title=title,
                                            content_length=len(self._clean_html_content(content)),
                                            order=chapter_order
                                        ))
                                        chapter_order += 1
                                except Exception as e:
                                    print(f"处理文档项目时出错: {e}")
                                    continue
                except Exception as e:
                    print(f"处理导航结构时出错: {e}")
                    # 如果导航结构处理失败，至少返回基本的章节信息
                    chapters = []
            
            # 如果最终没有找到任何章节，使用备用策略：直接从所有文档项创建章节
            if not chapters:
                print("使用备用策略：从所有文档项创建章节")
                chapter_order = 0
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        try:
                            content = item.get_content().decode('utf-8')
                            if content.strip():  # 只有非空内容才算章节
                                soup = BeautifulSoup(content, 'html.parser')
                                title = self._extract_chapter_title(soup, item.get_name())
                                # 使用Name作为ID
                                chapter_id = item.get_name() or item.get_id() or f"chapter_{chapter_order}"
                                chapters.append(ChapterInfo(
                                    id=chapter_id,
                                    title=title,
                                    content_length=len(self._clean_html_content(content)),
                                    order=chapter_order
                                ))
                                chapter_order += 1
                        except Exception as e:
                            print(f"处理备用文档项时出错: {e}")
                            continue
        
        except Exception as e:
            print(f"章节提取完全失败: {e}")
            # 使用最基础的备用策略：直接从所有文档项创建章节
            chapters = []
            chapter_order = 0
            try:
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        try:
                            content = item.get_content().decode('utf-8')
                            if content.strip():  # 只有非空内容才算章节
                                soup = BeautifulSoup(content, 'html.parser')
                                title = self._extract_chapter_title(soup, item.get_name())
                                # 使用Name作为ID
                                chapter_id = item.get_name() or item.get_id() or f"chapter_{chapter_order}"
                                chapters.append(ChapterInfo(
                                    id=chapter_id,
                                    title=title,
                                    content_length=len(self._clean_html_content(content)),
                                    order=chapter_order
                                ))
                                chapter_order += 1
                                if chapter_order >= 50:  # 限制章节数量，避免过多
                                    break
                        except Exception:
                            continue
            except Exception as final_e:
                print(f"备用策略也失败: {final_e}")
                # 最后的兜底：至少创建一个基于实际文件的章节
                if book.get_items():
                    first_item = next((item for item in book.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT), None)
                    if first_item:
                        # 使用Name作为ID
                        chapter_id = first_item.get_name() or first_item.get_id() or "chapter_0"
                        chapters = [ChapterInfo(
                            id=chapter_id,
                            title=first_item.get_name().replace('.html', '').replace('.xhtml', '').title(),
                            content_length=0,
                            order=0
                        )]
        
        return chapters
    
    def _extract_from_toc(self, toc, start_order: int = 0, book_id: str = None) -> List[ChapterInfo]:
        """从目录结构提取章节"""
        chapters = []
        order = start_order
        
        def extract_title_from_link(link_obj):
            """从Link对象提取标题"""
            try:
                if hasattr(link_obj, 'title') and link_obj.title:
                    return link_obj.title
                elif hasattr(link_obj, 'href'):
                    # 从href提取文件名作为标题
                    href = link_obj.href.split('#')[0]
                    return href.replace('.xhtml', '').replace('.html', '').replace('_', ' ').title()
                else:
                    return "Unknown Chapter"
            except Exception:
                return "Unknown Chapter"
        
        def process_toc_item(item, current_order):
            """递归处理TOC项目"""
            try:
                if isinstance(item, tuple):
                    # 处理元组格式 (Link, title, [children])
                    if len(item) >= 2:
                        link_obj = item[0]
                        title_obj = item[1]
                        
                        # 提取标题
                        if isinstance(title_obj, str):
                            title = title_obj
                        elif hasattr(title_obj, 'title'):
                            title = title_obj.title
                        else:
                            title = extract_title_from_link(link_obj)
                        
                        # 提取href
                        if hasattr(link_obj, 'href'):
                            href = link_obj.href.split('#')[0]
                            try:
                                content = self.get_chapter_content_by_href(link_obj.href, book_id)
                                content_length = len(content)
                            except Exception:
                                content_length = 0
                            
                            chapters.append(ChapterInfo(
                                id=href,
                                title=title,
                                content_length=content_length,
                                order=current_order
                            ))
                            current_order += 1
                        
                        # 处理子项目
                        if len(item) > 2 and isinstance(item[2], list):
                            for child in item[2]:
                                current_order = process_toc_item(child, current_order)
                
                elif hasattr(item, 'href'):
                    # 直接的Link对象
                    title = extract_title_from_link(item)
                    href = item.href.split('#')[0]
                    try:
                        content = self.get_chapter_content_by_href(item.href, book_id)
                        content_length = len(content)
                    except Exception:
                        content_length = 0
                    
                    chapters.append(ChapterInfo(
                        id=href,
                        title=title,
                        content_length=content_length,
                        order=current_order
                    ))
                    current_order += 1
                
                elif isinstance(item, str):
                    # 字符串标题
                    chapters.append(ChapterInfo(
                        id=f"chapter_{current_order}",
                        title=item,
                        content_length=0,
                        order=current_order
                    ))
                    current_order += 1
                
                # 如果是其他类型，静默跳过
            except Exception as e:
                # 如果处理某个项目出错，跳过它并继续
                print(f"处理TOC项目时出错: {e}")
            
            return current_order
        
        try:
            current_order = order
            for item in toc:
                current_order = process_toc_item(item, current_order)
        except Exception as e:
            print(f"处理TOC时出错: {e}")
        
        return chapters
    
    def _extract_chapter_title(self, soup: BeautifulSoup, default_name: str) -> str:
        """从HTML内容提取章节标题"""
        # 简单可靠的标题提取
        for tag in ['h1', 'h2', 'h3']:
            title_elem = soup.find(tag)
            if title_elem and title_elem.get_text().strip():
                title_text = title_elem.get_text().strip()
                # 基本过滤：不要太长、不要纯数字、不要包含换行
                if 3 <= len(title_text) <= 100 and not title_text.isdigit() and '\n' not in title_text:
                    return title_text
        
        # 如果没有找到合适的标题，从文件名生成
        clean_name = default_name.replace('.xhtml', '').replace('.html', '')
        clean_name = clean_name.replace('text/', '').replace('Text/', '')
        
        # 简单的数字提取和格式化
        import re
        number_match = re.search(r'(\d+)', clean_name)
        if number_match:
            chapter_num = int(number_match.group(1))
            return f"Chapter {chapter_num}"
        
        # 最后的兜底
        return "Untitled Chapter"
    
    def _is_content_chapter(self, item, soup: BeautifulSoup, content: str) -> bool:
        """判断是否是真正的内容章节"""
        item_name = item.get_name().lower()
        
        # 排除标题页、版权页、目录等
        skip_keywords = [
            'titlepage', 'copyright', 'toc', 'contents', 'nav',
            'index', 'bibliography', 'acknowledgment', 'preface',
            'cover', 'frontmatter', 'backmatter'
        ]
        
        for keyword in skip_keywords:
            if keyword in item_name:
                print(f"跳过非内容页面: {item_name} (包含关键字: {keyword})")
                return False
        
        # 检查内容长度 - 太短的通常不是正文章节
        text_content = soup.get_text().strip()
        if len(text_content) < 500:  # 少于500字符的内容通常不是正文
            print(f"跳过短内容: {item_name} (长度: {len(text_content)})")
            return False
        
        # 检查是否主要是Part标题或目录 - 如果主要内容都是链接，通常不是正文
        links = soup.find_all('a')
        if len(links) > 10 and len(text_content) < 2000:  # 很多链接且内容不多的页面
            link_text = ' '.join([a.get_text() for a in links])
            if len(link_text) / len(text_content) > 0.5:  # 链接文本占比超过一半
                print(f"跳过目录页面: {item_name} (链接占比过高)")
                return False
        
        # 如果标题包含Part字样且内容较短，可能是分节页
        title = self._extract_chapter_title(soup, item_name)
        if title.lower().startswith('part ') and len(text_content) < 1000:
            print(f"跳过分节页面: {item_name} (Part标题且内容较短)")
            return False
        
        return True

    def _clean_html_content(self, html_content: str) -> str:
        """清理HTML内容，保持基本格式"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除脚本和样式标签
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 移除不必要的属性，但保留基本结构
        for tag in soup.find_all():
            # 保留重要的格式标签
            if tag.name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b', 'em', 'i', 'u', 'br', 'div', 'span']:
                # 清理属性，只保留class（如果需要的话）
                attrs_to_keep = {}
                if 'class' in tag.attrs and any(cls in ['chapter', 'title', 'paragraph', 'quote'] for cls in tag.get('class', [])):
                    attrs_to_keep['class'] = tag.attrs['class']
                tag.attrs = attrs_to_keep
            else:
                # 对于其他标签，移除所有属性
                tag.attrs = {}
        
        # 返回格式化的HTML
        formatted_html = str(soup)
        
        # 如果仍然需要纯文本作为备选，可以这样处理
        # text = soup.get_text()
        # text = re.sub(r'\s+', ' ', text).strip()
        
        return formatted_html
    
    def get_all_books(self) -> List[BookInfo]:
        """获取所有已上传的书籍列表"""
        books = []
        book_info_dir = os.path.join(self.storage_path, 'book_info')
        
        if not os.path.exists(book_info_dir):
            return books
        
        # 遍历所有书籍信息文件
        for filename in os.listdir(book_info_dir):
            if filename.endswith('.json'):
                book_id = filename[:-5]  # 移除.json后缀
                try:
                    book_info = self._load_book_info(book_id)
                    if book_info:
                        books.append(book_info)
                except Exception as e:
                    print(f"加载书籍信息失败 {book_id}: {str(e)}")
                    continue
        
        # 按上传时间排序（最新的在前）
        books.sort(key=lambda x: x.upload_time, reverse=True)
        return books
    
    def get_book_info(self, book_id: str) -> BookInfo:
        """获取单个书籍信息"""
        book_info = self._load_book_info(book_id)
        if not book_info:
            raise Exception(f"书籍不存在: {book_id}")
        return book_info
    
    def delete_book(self, book_id: str) -> None:
        """删除书籍及其相关文件"""
        try:
            print(f"开始删除书籍: {book_id}")
            
            # 获取书籍信息
            book_info = self._load_book_info(book_id)
            if not book_info:
                raise Exception(f"书籍不存在: {book_id}")
            
            print(f"找到书籍信息: {book_info.title}")
            
            # 删除EPUB文件
            if book_info.file_path and os.path.exists(book_info.file_path):
                try:
                    os.remove(book_info.file_path)
                    print(f"已删除EPUB文件: {book_info.file_path}")
                except Exception as e:
                    print(f"删除EPUB文件失败: {e}")
            else:
                print(f"EPUB文件不存在或路径为空: {book_info.file_path}")
            
            # 删除书籍信息文件
            book_info_file = os.path.join(self.storage_path, 'book_info', f'{book_id}.json')
            if os.path.exists(book_info_file):
                try:
                    os.remove(book_info_file)
                    print(f"已删除书籍信息文件: {book_info_file}")
                except Exception as e:
                    print(f"删除书籍信息文件失败: {e}")
            else:
                print(f"书籍信息文件不存在: {book_info_file}")
            
            # 删除翻译文件夹（如果存在）
            translation_dir_path = os.path.join(settings.translation_dir, book_id)
            if os.path.exists(translation_dir_path):
                try:
                    import shutil
                    shutil.rmtree(translation_dir_path)
                    print(f"已删除翻译文件夹: {translation_dir_path}")
                except Exception as e:
                    print(f"删除翻译文件夹失败: {e}")
            else:
                print(f"翻译文件夹不存在: {translation_dir_path}")
            
            # 删除音频文件夹（如果存在）
            audio_dir = os.path.join(settings.audio_dir, book_id)
            if os.path.exists(audio_dir):
                try:
                    import shutil
                    shutil.rmtree(audio_dir)
                    print(f"已删除音频文件夹: {audio_dir}")
                except Exception as e:
                    print(f"删除音频文件夹失败: {e}")
            else:
                print(f"音频文件夹不存在: {audio_dir}")
            
            # 从内存中移除
            if book_id in self.parsed_books:
                del self.parsed_books[book_id]
                print(f"已从内存中移除书籍: {book_id}")
            
            print(f"书籍 {book_id} 删除成功")
            
        except Exception as e:
            print(f"删除书籍失败: {str(e)}")
            raise Exception(f"删除书籍失败: {str(e)}")
    
    def get_chapters(self, book_id: str) -> List[ChapterInfo]:
        """获取书籍的章节列表"""
        book_info = self._load_book_info(book_id)
        if not book_info:
            raise Exception(f"找不到书籍: {book_id}")
        
        return book_info.chapters
    
    def get_chapter_content(self, book_id: str, chapter_id: str) -> str:
        """获取章节的原始内容"""
        print(f"尝试获取章节内容 - book_id: {book_id}, chapter_id: {chapter_id}")
        
        if book_id not in self.parsed_books:
            # 重新加载书籍
            book_info = self._load_book_info(book_id)
            if not book_info:
                raise Exception(f"找不到书籍: {book_id}")
            
            print(f"重新加载书籍: {book_info.file_path}")
            book = epub.read_epub(book_info.file_path)
            self.parsed_books[book_id] = book
        
        book = self.parsed_books[book_id]
        
        # 打印所有可用的章节项以便调试
        print("可用的章节项:")
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                print(f"  - ID: {item.get_id()}, Name: {item.get_name()}")
        
        # 查找对应的章节
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # 尝试多种匹配方式
                if (item.get_id() == chapter_id or 
                    item.get_name() == chapter_id or
                    item.get_name() == f"{chapter_id}" or
                    item.get_name().endswith(chapter_id)):
                    
                    print(f"找到匹配的章节: {item.get_name()}")
                    content = item.get_content().decode('utf-8')
                    cleaned_content = self._clean_html_content(content)
                    print(f"章节内容长度: {len(cleaned_content)}")
                    return cleaned_content
        
        # 如果直接匹配失败，尝试模糊匹配
        chapter_id_lower = chapter_id.lower()
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                if (chapter_id_lower in item.get_name().lower() or 
                    chapter_id_lower in (item.get_id() or "").lower()):
                    
                    print(f"模糊匹配找到章节: {item.get_name()}")
                    content = item.get_content().decode('utf-8')
                    cleaned_content = self._clean_html_content(content)
                    return cleaned_content
        
        print(f"未找到章节: {chapter_id}")
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