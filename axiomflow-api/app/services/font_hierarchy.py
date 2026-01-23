"""
字体层次结构分析模块

分析字体大小、样式、族等特征，用于识别文档结构（标题、正文、脚注、公式等）。
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass
class FontStyle:
    """字体样式信息"""
    name: str
    size: float
    flags: int | None = None  # 粗体、斜体等标志
    is_bold: bool = False
    is_italic: bool = False
    is_code: bool = False
    is_math: bool = False


class FontHierarchyAnalyzer:
    """字体层次结构分析器"""
    
    # 数学字体模式（与formula_detect.py保持一致）
    MATH_FONT_PATTERNS = [
        r"(CM[^R]|MS\.M|XY|MT|BL|RM|EU|LA|RS|LINE|LCIRCLE)",
        r"TeX-.*",
        r"(rsfs|txsy|wasy|stmary)",
        r".*Mono.*",
        r".*Code.*",
        r".*Ital.*",
        r".*Sym.*",
        r".*Math.*",
    ]
    
    # 代码字体模式
    CODE_FONT_PATTERNS = [
        r".*Mono.*",
        r".*Code.*",
        r"Courier",
        r"Consolas",
    ]
    
    def __init__(self):
        self.font_styles: list[FontStyle] = []
        self.size_hierarchy: dict[str, float] = {}  # 类型 -> 平均字体大小
    
    def analyze_block(self, block: dict[str, Any]) -> dict[str, Any]:
        """
        分析单个block的字体信息
        
        Args:
            block: 文本块字典（包含font字段）
        
        Returns:
            分析结果字典
        """
        font_dict = block.get("font")
        if not font_dict:
            return {"style": None, "level": "unknown"}
        
        font_name = font_dict.get("name", "")
        font_size = font_dict.get("size")
        
        if not font_size:
            return {"style": None, "level": "unknown"}
        
        # 分析字体特征
        style = FontStyle(
            name=font_name,
            size=font_size,
        )
        
        # 检测数学字体
        style.is_math = self._is_math_font(font_name)
        
        # 检测代码字体
        style.is_code = self._is_code_font(font_name)
        
        # 检测粗体、斜体（如果font_dict中有flags）
        if "flags" in font_dict:
            flags = font_dict["flags"]
            style.flags = flags
            style.is_bold = bool(flags & 0x00000001)  # 粗体标志
            style.is_italic = bool(flags & 0x00000002)  # 斜体标志
        
        # 确定层级（标题、正文、脚注）
        level = self._determine_level(style, block)
        
        return {
            "style": style,
            "level": level,
            "is_math": style.is_math,
            "is_code": style.is_code,
            "is_bold": style.is_bold,
            "is_italic": style.is_italic,
        }
    
    def _is_math_font(self, font_name: str) -> bool:
        """判断是否为数学字体"""
        if not font_name:
            return False
        
        font_base = font_name.split("+")[-1].strip()
        
        for pattern in self.MATH_FONT_PATTERNS:
            if re.match(pattern, font_base, re.IGNORECASE):
                return True
        
        return False
    
    def _is_code_font(self, font_name: str) -> bool:
        """判断是否为代码字体"""
        if not font_name:
            return False
        
        font_base = font_name.split("+")[-1].strip()
        
        for pattern in self.CODE_FONT_PATTERNS:
            if re.match(pattern, font_base, re.IGNORECASE):
                return True
        
        return False
    
    def _determine_level(self, style: FontStyle, block: dict[str, Any]) -> str:
        """
        确定文本块层级（标题、正文、脚注等）
        
        Args:
            style: 字体样式
            block: 文本块
        
        Returns:
            "heading" | "body" | "caption" | "footnote" | "unknown"
        """
        font_size = style.size
        
        # 如果没有大小信息，使用启发式
        if not font_size:
            block_type = block.get("type", "")
            if block_type == "heading":
                return "heading"
            elif block_type == "caption":
                return "caption"
            elif block.get("is_footnote"):
                return "footnote"
            return "body"
        
        # 基于字体大小判断
        # 注意：这里的阈值需要根据实际文档调整
        if font_size >= 14:
            # 大字体：可能是标题
            if style.is_bold:
                return "heading"
            else:
                return "body"  # 也可能是大正文
        elif font_size <= 9:
            # 小字体：可能是脚注或角标
            if block.get("is_footnote"):
                return "footnote"
            return "footnote"
        else:
            # 正常大小：正文
            if block.get("type") == "caption":
                return "caption"
            return "body"
    
    def analyze_document(self, pages: list[dict[str, Any]]) -> dict[str, Any]:
        """
        分析整个文档的字体层次结构
        
        Args:
            pages: 页面列表（每个页面包含blocks）
        
        Returns:
            文档级别的字体层次分析结果
        """
        all_sizes: list[float] = []
        font_counter: Counter[str] = Counter()
        level_counter: Counter[str] = Counter()
        
        for page in pages:
            blocks = page.get("blocks", [])
            for block in blocks:
                analysis = self.analyze_block(block)
                
                style = analysis.get("style")
                if style and style.size:
                    all_sizes.append(style.size)
                    font_counter[style.name] += 1
                    level_counter[analysis["level"]] += 1
        
        # 计算字体大小统计
        if all_sizes:
            avg_size = sum(all_sizes) / len(all_sizes)
            min_size = min(all_sizes)
            max_size = max(all_sizes)
            
            # 识别大小层次
            unique_sizes = sorted(set(all_sizes))
            size_tiers = {}
            if len(unique_sizes) >= 3:
                size_tiers["heading"] = max_size
                size_tiers["body"] = avg_size
                size_tiers["footnote"] = min_size
            elif len(unique_sizes) >= 2:
                size_tiers["heading"] = max_size
                size_tiers["body"] = min_size
        else:
            avg_size = 0
            min_size = 0
            max_size = 0
            size_tiers = {}
        
        return {
            "avg_font_size": avg_size,
            "min_font_size": min_size,
            "max_font_size": max_size,
            "size_tiers": size_tiers,
            "font_distribution": dict(font_counter.most_common(10)),
            "level_distribution": dict(level_counter),
        }

