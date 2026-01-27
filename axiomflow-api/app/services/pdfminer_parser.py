"""
PDFMiner 字符级深度解析模块

提供字符级别的精确解析，用于复杂区域（公式、表格、CJK文本）的深度分析。
增强版：支持 fontid/fontmap 深度追踪，提升字体识别精度。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

try:
    from pdfminer.converter import PDFConverter
    from pdfminer.layout import LTChar, LTFigure, LTPage, LTTextLine
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage
    from pdfminer.utils import apply_matrix_pt
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdffont import PDFFont
    from pdfminer.pdftypes import PDFObjRef, dict_value
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False
    # 提供占位符以避免导入错误
    PDFConverter = None
    LTChar = None
    LTPage = None
    PDFFont = None
    PDFObjRef = None

logger = logging.getLogger(__name__)


@dataclass
class CharInfo:
    """字符级信息（增强版：包含 fontid 追踪）"""
    char: str
    x0: float
    y0: float
    x1: float
    y1: float
    font_name: str
    font_size: float
    font_flags: int  # 粗体、斜体等标志
    cid: int | None = None  # 字符ID（用于CID字体）
    fontid: str | None = None  # PDF字体资源ID（增强：字体映射追踪）
    font_objid: int | None = None  # 字体对象的PDF对象ID


@dataclass
class CharLevelBlock:
    """字符级文本块"""
    text: str
    chars: list[CharInfo]
    x0: float
    y0: float
    x1: float
    y1: float
    page_index: int


class PDFPageInterpreterEx(PDFPageInterpreter):
    """
    增强的 PDF 页面解释器：追踪 fontid 和 fontmap
    
    重载 init_resources 方法以建立字体ID到字体对象的映射关系，
    从而支持更精确的字体识别和追踪。
    """
    
    def __init__(self, rsrcmgr: PDFResourceManager, device: PDFConverter):
        super().__init__(rsrcmgr, device)
        # 字体映射：fontid -> PDFFont
        self.fontmap: Dict[object, PDFFont] = {}
        # 反向映射：PDFFont -> fontid
        self.fontid: Dict[PDFFont, object] = {}
    
    def init_resources(self, resources: Dict[object, object]) -> None:
        """重载资源初始化：追踪字体映射"""
        # 调用父类方法
        super().init_resources(resources)
        
        # 建立 fontid/fontmap 映射
        if not resources:
            return
        
        try:
            for k, v in dict_value(resources).items():
                if k == "Font":
                    for fontid, spec in dict_value(v).items():
                        objid = None
                        if isinstance(spec, PDFObjRef):
                            objid = spec.objid
                        spec = dict_value(spec)
                        font = self.rsrcmgr.get_font(objid, spec)
                        
                        # 建立双向映射
                        self.fontmap[fontid] = font
                        self.fontid[font] = fontid
                        
                        # 可选：修复 descent（某些PDF可能有问题）
                        if hasattr(font, "descent"):
                            try:
                                font.descent = 0  # hack fix descent
                            except Exception:
                                pass
        except Exception as e:
            logger.debug(f"初始化字体映射时出错（已忽略）: {e}")


class CharacterLevelConverter(PDFConverter):
    """
    字符级转换器：提取每个字符的详细信息（增强版：支持 fontid 追踪）
    """
    
    def __init__(self, rsrcmgr: PDFResourceManager, interpreter: PDFPageInterpreterEx | None = None):
        if not PDFMINER_AVAILABLE:
            raise ImportError("pdfminer.six 未安装，无法使用字符级解析")
        PDFConverter.__init__(self, rsrcmgr, None, "utf-8", 1, None)
        self.chars: list[CharInfo] = []
        self.page_index = 0
        # 保存 interpreter 引用以访问 fontid/fontmap
        self.interpreter = interpreter
    
    def begin_page(self, page, ctm):
        """开始页面"""
        (x0, y0, x1, y1) = page.cropbox
        (x0, y0) = apply_matrix_pt(ctm, (x0, y0))
        (x1, y1) = apply_matrix_pt(ctm, (x1, y1))
        mediabox = (0, 0, abs(x0 - x1), abs(y0 - y1))
        # 使用存储的 page_index，因为新版本的 pdfminer 可能没有 page.pageno 属性
        # 如果 page_index 未设置，尝试从 page 对象获取，否则使用 0
        page_no = self.page_index if hasattr(self, 'page_index') else (getattr(page, 'pageno', None) or getattr(page, 'pageid', None) or 0)
        self.cur_item = LTPage(page_no, mediabox)
        self.page_index = page_no
    
    def render_char(
        self,
        matrix,
        font,
        fontsize: float,
        scaling: float,
        rise: float,
        cid: int,
        ncs,
        graphicstate,
    ) -> float:
        """渲染字符：提取字符级信息"""
        try:
            from pdfminer.pdffont import PDFUnicodeNotDefined
            
            # 获取字符文本
            try:
                text = font.to_unichr(cid)
            except PDFUnicodeNotDefined:
                text = self.handle_undefined_char(font, cid)
            
            # 计算字符位置
            textwidth = font.char_width(cid)
            textdisp = font.char_disp(cid)
            
            # 应用变换矩阵计算实际位置
            (a, b, c, d, e, f) = matrix
            x0 = e
            y0 = f
            x1 = e + textwidth * fontsize
            y1 = f + fontsize
            
            # 获取字体信息
            font_name = getattr(font, "fontname", "")
            if isinstance(font_name, bytes):
                try:
                    font_name = font_name.decode("utf-8")
                except UnicodeDecodeError:
                    font_name = str(font_name)
            
            # 获取字体标志（粗体、斜体等）
            font_flags = getattr(font, "flags", 0)
            
            # 获取 fontid（从 interpreter 的映射中查找）
            fontid = None
            font_objid = None
            if self.interpreter and hasattr(self.interpreter, "fontid"):
                # 从 fontid 映射中查找
                fontid = self.interpreter.fontid.get(font)
                # 尝试获取字体对象的 PDF 对象ID
                if hasattr(font, "objid"):
                    font_objid = font.objid
            
            # 如果 fontid 是 bytes，转换为字符串
            if isinstance(fontid, bytes):
                try:
                    fontid = fontid.decode("utf-8", errors="replace")
                except Exception:
                    fontid = str(fontid)
            elif fontid is not None:
                fontid = str(fontid)
            
            # 创建字符信息（增强版：包含 fontid）
            char_info = CharInfo(
                char=text,
                x0=x0,
                y0=y0,
                x1=x1,
                y1=y1,
                font_name=font_name,
                font_size=fontsize,
                font_flags=font_flags,
                cid=cid if hasattr(font, "cid") else None,
                fontid=fontid,
                font_objid=font_objid,
            )
            
            self.chars.append(char_info)
            
            # 创建LTChar对象（保持兼容）
            item = LTChar(
                matrix,
                font,
                fontsize,
                scaling,
                rise,
                text,
                textwidth,
                textdisp,
                ncs,
                graphicstate,
            )
            self.cur_item.add(item)
            
            return item.adv
        
        except Exception as e:
            logger.warning(f"字符渲染失败: {e}")
            return 0.0


def extract_chars_from_pdf(pdf_path: Path, page_index: int) -> list[CharInfo]:
    """
    从PDF指定页面提取字符级信息（增强版：支持 fontid 追踪）
    
    Args:
        pdf_path: PDF文件路径
        page_index: 页面索引（从0开始）
    
    Returns:
        字符信息列表（包含 fontid 信息）
    """
    if not PDFMINER_AVAILABLE:
        logger.warning("pdfminer.six 未安装，无法使用字符级解析")
        return []
    
    try:
        with open(pdf_path, "rb") as fp:
            parser = PDFParser(fp)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            
            # 使用增强的解释器和转换器
            converter = CharacterLevelConverter(rsrcmgr, interpreter=None)
            interpreter_ex = PDFPageInterpreterEx(rsrcmgr, converter)
            # 设置 converter 的 interpreter 引用
            converter.interpreter = interpreter_ex
            
            # 找到指定页面
            pages = list(PDFPage.create_pages(doc))
            if page_index >= len(pages):
                return []
            
            # 设置转换器的页面索引（页码从1开始，但索引从0开始）
            converter.page_index = page_index + 1
            page = pages[page_index]
            interpreter_ex.process_page(page)
            
            return converter.chars
    
    except Exception as e:
        logger.error(f"PDFMiner解析失败: {e}", exc_info=True)
        return []


def extract_chars_from_region(
    pdf_path: Path,
    page_index: int,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> list[CharInfo]:
    """
    从PDF指定区域的页面提取字符级信息
    
    Args:
        pdf_path: PDF文件路径
        page_index: 页面索引
        x0, y0, x1, y1: 区域边界
    
    Returns:
        区域内的字符信息列表
    """
    all_chars = extract_chars_from_pdf(pdf_path, page_index)
    
    # 过滤区域内的字符
    region_chars = [
        char
        for char in all_chars
        if (
            char.x0 >= x0 - 5  # 允许5pt误差
            and char.y0 >= y0 - 5
            and char.x1 <= x1 + 5
            and char.y1 <= y1 + 5
        )
    ]
    
    return region_chars


def group_chars_into_blocks(chars: list[CharInfo], page_index: int) -> list[CharLevelBlock]:
    """
    将字符分组为文本块（按行分组）
    
    Args:
        chars: 字符列表
        page_index: 页面索引
    
    Returns:
        字符级文本块列表
    """
    if not chars:
        return []
    
    # 按y坐标分组（同一行的字符）
    lines: dict[float, list[CharInfo]] = {}
    
    for char in chars:
        # 使用y0作为行的关键（允许1pt误差）
        line_key = round(char.y0 / 1.0) * 1.0
        
        if line_key not in lines:
            lines[line_key] = []
        lines[line_key].append(char)
    
    # 按y坐标排序（从上到下）
    sorted_lines = sorted(lines.items(), key=lambda x: x[0], reverse=True)
    
    blocks: list[CharLevelBlock] = []
    
    for line_y, line_chars in sorted_lines:
        # 按x坐标排序（从左到右）
        line_chars.sort(key=lambda c: c.x0)
        
        if not line_chars:
            continue
        
        # 计算行的边界
        line_x0 = min(c.x0 for c in line_chars)
        line_y0 = min(c.y0 for c in line_chars)
        line_x1 = max(c.x1 for c in line_chars)
        line_y1 = max(c.y1 for c in line_chars)
        
        # 合并文本
        text = "".join(c.char for c in line_chars)
        
        block = CharLevelBlock(
            text=text,
            chars=line_chars,
            x0=line_x0,
            y0=line_y0,
            x1=line_x1,
            y1=line_y1,
            page_index=page_index,
        )
        
        blocks.append(block)
    
    return blocks


def analyze_font_pattern(chars: list[CharInfo]) -> dict[str, Any]:
    """
    分析字符列表的字体模式（增强版：包含 fontid 统计）
    
    Args:
        chars: 字符列表
    
    Returns:
        字体模式分析结果（包含 fontid 映射信息）
    """
    if not chars:
        return {}
    
    from collections import Counter
    
    # 统计字体名称
    font_names = Counter(c.font_name for c in chars)
    
    # 统计字体大小
    font_sizes = [c.font_size for c in chars]
    avg_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0
    
    # 检测字体大小突变（角标）
    size_variations = []
    if len(chars) > 1:
        for i in range(1, len(chars)):
            size_ratio = chars[i].font_size / chars[i-1].font_size
            size_variations.append(size_ratio)
    
    has_subscript_superscript = any(
        0.5 < ratio < 0.9 or 1.1 < ratio < 1.5 for ratio in size_variations
    )
    
    # 统计字体标志（粗体、斜体）
    font_flags = Counter(c.font_flags for c in chars)
    
    # 统计 fontid（增强：字体ID分布）
    fontids = Counter(c.fontid for c in chars if c.fontid is not None)
    
    # 建立 fontid -> font_name 的映射（用于追踪）
    fontid_to_name: dict[str, str] = {}
    for c in chars:
        if c.fontid and c.fontid not in fontid_to_name:
            fontid_to_name[c.fontid] = c.font_name
    
    return {
        "font_names": dict(font_names.most_common()),
        "most_common_font": font_names.most_common(1)[0][0] if font_names else "",
        "avg_font_size": avg_size,
        "has_size_variation": has_subscript_superscript,
        "font_flags_distribution": dict(font_flags),
        "char_count": len(chars),
        # 增强：fontid 相关统计
        "fontid_distribution": dict(fontids.most_common()),
        "fontid_to_name_map": fontid_to_name,
        "unique_fontids": len(fontids),
    }

