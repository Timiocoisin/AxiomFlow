"""
字体子集化模块

使用 fonttools 实现精确的字体子集化，只保留PDF中实际使用的字符，
显著减小PDF文件体积。
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Set


def collect_used_characters(structured: dict) -> Set[str]:
    """
    从结构化文档中收集所有使用的字符。
    
    Args:
        structured: 结构化文档 JSON
    
    Returns:
        使用的字符集合
    """
    used_chars: Set[str] = set()
    
    pages = structured.get("pages", [])
    for page in pages:
        blocks = page.get("blocks", [])
        for block in blocks:
            # 收集原文和译文中的所有字符
            text = block.get("text", "")
            translation = block.get("translation", "")
            
            if text:
                used_chars.update(text)
            if translation:
                used_chars.update(translation)
    
    return used_chars


def create_font_subset(
    font_path: str,
    used_chars: Set[str],
    output_path: str | None = None,
) -> str:
    """
    创建字体子集，只包含使用的字符。
    
    Args:
        font_path: 原始字体文件路径
        used_chars: 使用的字符集合
        output_path: 输出路径（如果为 None，则创建临时文件）
    
    Returns:
        子集化字体文件路径
    """
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError:
        # 如果 fonttools 未安装，返回原字体路径
        # 注意：需要在依赖中添加 fonttools
        return font_path
    
    try:
        # 加载字体
        font = TTFont(font_path)
        
        # 将字符转换为 Unicode 码点列表
        unicodes = {ord(char) for char in used_chars if ord(char) <= 0x10FFFF}
        
        # 如果未指定输出路径，创建临时文件
        if output_path is None:
            suffix = Path(font_path).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                output_path = tmp.name
        
        # 配置子集化选项
        options = subset.Options()
        
        # 保留字形名称（便于调试）
        options.glyph_names = True
        
        # 保留 GID（字形 ID）
        options.retain_gids = False
        
        # 保留 .notdef 字形（未定义字符的占位符）
        options.notdef_glyph = True
        
        # 保留推荐字形（基本标点、数字、字母等）
        options.recommended_glyphs = True
        
        # 保留名称表（字体名称信息）
        options.name_IDs = ['*']
        options.name_legacy = True
        
        # 保留布局特性（OpenType features）
        options.layout_features = ['*']
        
        # 保留提示信息（hinting）
        options.hinting = True
        
        # 对于 TTC (TrueType Collection) 字体，需要特殊处理
        if font.sfntVersion == 'OTTO':  # OpenType with CFF
            options.desubroutinize = True
        
        # 创建子集器
        subsetter = subset.Subsetter(options=options)
        
        # 设置要保留的 Unicode 字符
        subsetter.populate(unicodes=unicodes)
        
        # 执行子集化
        subsetter.subset(font)
        
        # 保存子集化字体
        font.save(output_path)
        font.close()
        
        return output_path
    
    except Exception:
        # 如果子集化失败，返回原字体路径
        return font_path


def optimize_font_embedding(
    pdf_doc,
    *,
    subset_fonts: bool = True,
    used_chars: Set[str] | None = None,
) -> None:
    """
    优化PDF中的字体嵌入。
    
    Args:
        pdf_doc: PyMuPDF Document 对象
        subset_fonts: 是否进行字体子集化
        used_chars: 使用的字符集合（如果为 None，则从PDF中提取）
    """
    if not subset_fonts:
        # 如果不子集化，使用 PyMuPDF 的默认方法
        try:
            pdf_doc.subset_fonts(fallback=True)
        except Exception:
            pass
        return
    
    try:
        # 使用 PyMuPDF 的内置子集化（这会自动提取使用的字符）
        # 这是最可靠的方法，因为 PyMuPDF 知道实际渲染的字符
        pdf_doc.subset_fonts(fallback=True)
        
        # 注意：PyMuPDF 的 subset_fonts() 已经相当完善，
        # 它会自动提取PDF中实际使用的字符并进行子集化。
        # 如果需要对自定义嵌入的字体进行更精确控制，
        # 可以在插入文本之前先创建子集化字体。
    
    except Exception:
        # 如果子集化失败，尝试使用更宽松的选项
        try:
            pdf_doc.subset_fonts(fallback=False)
        except Exception:
            pass


def get_font_info_from_pdf(pdf_path: str) -> list[dict]:
    """
    从PDF中提取字体信息。
    
    Args:
        pdf_path: PDF文件路径
    
    Returns:
        字体信息列表，每个字典包含：
        - name: 字体名称
        - embedded: 是否已嵌入
        - subset: 是否为子集
        - encoding: 编码方式
    """
    import fitz  # PyMuPDF
    
    font_info_list = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            
            # 获取页面字体列表
            fonts = page.get_fonts()
            
            for font_item in fonts:
                font_info_list.append({
                    "name": font_item.get("name", ""),
                    "ext": font_item.get("ext", ""),
                    "type": font_item.get("type", ""),
                    "embedded": font_item.get("embedded", 0) == 1,
                    "subset": font_item.get("embedded", 0) == 1 and font_item.get("subset", 0) == 1,
                    "page": page_num,
                })
        
        doc.close()
    
    except Exception:
        pass
    
    return font_info_list

