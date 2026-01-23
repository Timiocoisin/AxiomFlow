"""
公式识别模块

支持基于字体名称正则匹配（vfont）和符号密度的公式识别。
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Callable

from ..core.config_manager import config_manager


@dataclass
class FontInfo:
    """字体信息"""
    name: str
    size: float | None = None
    flags: int | None = None  # 字体标志（粗体、斜体等）


def _get_vfont_pattern() -> str | None:
    """
    获取 vfont 正则表达式模式（从配置读取）。
    
    如果没有配置，返回 None，使用默认规则。
    """
    vfont = config_manager.get("parser.vfont", "")
    if vfont and vfont.strip():
        return vfont.strip()
    return None


def _is_math_font_by_default(font_name: str) -> bool:
    """
    默认数学字体匹配规则（当 vfont 未配置时使用）。
    
    匹配常见的数学/公式字体：
    - CM (Computer Modern)
    - MS.M (Microsoft Math)
    - MT (MathType)
    - XY, BL, RM, EU, LA, RS, LINE, LCIRCLE (LaTeX 符号字体)
    - TeX-, rsfs, txsy, wasy, stmary (TeX 专用字体)
    - Mono, Code (等宽字体，常用于公式)
    - Ital, Italic (斜体，常用于公式)
    - Sym, Symbol, Math (明确标记为符号/数学的字体)
    """
    if not font_name:
        return False
    
    # 取字体名的最后一部分（处理 "Arial+MT" 这种情况）
    font_base = font_name.split("+")[-1].strip()
    
    default_patterns = [
        r"(CM[^R]|MS\.M|XY|MT|BL|RM|EU|LA|RS|LINE|LCIRCLE)",  # LaTeX 常见字体
        r"TeX-.*",  # TeX 字体前缀
        r"(rsfs|txsy|wasy|stmary)",  # TeX 专用符号字体
        r".*Mono.*",  # 等宽字体
        r".*Code.*",  # 代码字体
        r".*Ital.*",  # 斜体
        r".*Sym.*",  # 符号字体
        r".*Math.*",  # 数学字体
    ]
    
    for pattern in default_patterns:
        if re.match(pattern, font_base, re.IGNORECASE):
            return True
    
    return False


def _is_math_character(char: str) -> bool:
    """
    判断字符是否为数学符号。
    
    检查 Unicode 类别和特定范围：
    - Lm (字母修饰符)
    - Mn (非空格标记)
    - Sk (修饰符号)
    - Sm (数学符号)
    - Zl, Zp, Zs (分隔符)
    - 希腊字母范围 (0x370-0x400)
    """
    if not char or char == " ":
        return False
    
    cat = unicodedata.category(char[0])
    if cat in ["Lm", "Mn", "Sk", "Sm", "Zl", "Zp", "Zs"]:
        return True
    
    # 希腊字母范围
    if 0x370 <= ord(char[0]) < 0x400:
        return True
    
    return False


def detect_formula_by_font(
    text: str,
    font_info: FontInfo | None = None,
    vchar_pattern: str | None = None,
) -> tuple[bool, float]:
    """
    基于字体信息检测公式。
    
    Args:
        text: 文本内容
        font_info: 字体信息
        vchar_pattern: 字符正则表达式模式（可选）
    
    Returns:
        (is_formula, confidence): 是否为公式，置信度 (0-1)
    """
    if not text or not text.strip():
        return False, 0.0
    
    confidence = 0.0
    
    # 1. 字体名称匹配（最高优先级）
    if font_info and font_info.name:
        vfont_pattern = _get_vfont_pattern()
        
        if vfont_pattern:
            # 使用用户配置的 vfont 正则
            font_base = font_info.name.split("+")[-1].strip()
            if re.match(vfont_pattern, font_base, re.IGNORECASE):
                confidence = max(confidence, 0.9)
        else:
            # 使用默认数学字体规则
            if _is_math_font_by_default(font_info.name):
                confidence = max(confidence, 0.85)
    
    # 2. 字符模式匹配（vchar）
    if vchar_pattern:
        if re.search(vchar_pattern, text):
            confidence = max(confidence, 0.8)
    
    # 3. LaTeX 语法检测
    has_latex = (
        ("\\(" in text) or
        ("\\[" in text) or
        ("$$" in text) or
        ("$" in text and text.count("$") >= 2) or
        ("\\begin{" in text and "\\end{" in text)
    )
    if has_latex:
        confidence = max(confidence, 0.9)
    
    # 4. 数学符号密度
    math_symbols = set("=+-*/∑∏√≈≠≤≥→↔αβγδθλμσπ∞∂∇∫∬∭∮∯∰")
    math_symbol_count = sum(1 for ch in text if ch in math_symbols or _is_math_character(ch))
    
    if math_symbol_count >= 2:
        # 符号密度越高，置信度越高
        symbol_ratio = math_symbol_count / max(len(text), 1)
        if symbol_ratio > 0.3:
            confidence = max(confidence, min(0.95, 0.5 + symbol_ratio))
        elif symbol_ratio > 0.15:
            confidence = max(confidence, 0.6)
        else:
            confidence = max(confidence, 0.5)
    
    # 5. 非字母数字字符比例
    non_word_count = sum(1 for ch in text if not ch.isalnum() and not ch.isspace())
    non_word_ratio = non_word_count / max(len(text), 1)
    if non_word_ratio > 0.4:
        confidence = max(confidence, min(0.85, 0.4 + non_word_ratio * 0.5))
    
    # 综合判断
    is_formula = confidence >= 0.5
    
    return is_formula, confidence


def extract_fonts_from_text_dict(text_dict: dict) -> dict[int, FontInfo]:
    """
    从 PyMuPDF get_text("dict") 结果中提取字体信息。
    
    Args:
        text_dict: PyMuPDF page.get_text("dict") 返回的字典
    
    Returns:
        {block_index: FontInfo} 字典，包含每个 block 的字体信息
        注意：这里的 block_index 对应 get_text("dict") 中的文本块索引
    """
    fonts: dict[int, FontInfo] = {}
    
    blocks = text_dict.get("blocks", [])
    text_block_idx = 0  # 只计数文本块
    
    for block in blocks:
        if block.get("type") != 0:  # 0 表示文本块
            continue
        
        lines = block.get("lines", [])
        if not lines:
            text_block_idx += 1
            continue
        
        # 收集该 block 中所有出现的字体
        font_names: list[str] = []
        font_sizes: list[float] = []
        
        for line in lines:
            spans = line.get("spans", [])
            for span in spans:
                font_name = span.get("font", "")
                font_size = span.get("size", 0)
                if font_name:
                    font_names.append(font_name)
                    if font_size > 0:
                        font_sizes.append(font_size)
        
        # 取最常见的字体作为该 block 的代表字体
        if font_names:
            from collections import Counter
            font_counter = Counter(font_names)
            most_common_font = font_counter.most_common(1)[0][0]
            avg_size = sum(font_sizes) / len(font_sizes) if font_sizes else None
            
            fonts[text_block_idx] = FontInfo(
                name=most_common_font,
                size=avg_size,
            )
        
        text_block_idx += 1
    
    return fonts


def detect_formula_block(
    block: dict,
    font_info: FontInfo | None = None,
    vchar_pattern: str | None = None,
) -> bool:
    """
    检测单个 block 是否为公式。
    
    Args:
        block: block 字典（包含 text 字段）
        font_info: 字体信息（可选）
        vchar_pattern: 字符正则表达式模式（可选）
    
    Returns:
        是否为公式
    """
    text = (block.get("text") or "").strip()
    if not text:
        return False
    
    is_formula, confidence = detect_formula_by_font(text, font_info, vchar_pattern)
    
    # 可选：将置信度保存到 block 中
    if is_formula and "formula_confidence" not in block:
        block["formula_confidence"] = confidence
    
    return is_formula

