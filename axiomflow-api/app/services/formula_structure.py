"""
公式结构提取模块

从字符级解析结果中提取公式的结构化信息（LaTeX 表达式、子公式等）。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FormulaComponent:
    """公式组件（子公式、符号等）"""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    component_type: str  # "symbol", "number", "variable", "operator", "function"
    font_name: str | None = None
    font_size: float | None = None
    is_subscript: bool = False
    is_superscript: bool = False


@dataclass
class FormulaStructure:
    """公式结构"""
    original_text: str
    latex_expression: str | None
    components: list[FormulaComponent]
    has_fractions: bool = False
    has_superscripts: bool = False
    has_subscripts: bool = False
    has_integrals: bool = False
    has_summations: bool = False


def extract_formula_structure(
    chars: list[Any],  # CharInfo 列表
    region_text: str,
) -> FormulaStructure:
    """
    从字符列表提取公式结构
    
    Args:
        chars: 字符信息列表（CharInfo）
        region_text: 区域的原始文本
    
    Returns:
        公式结构
    """
    if not chars:
        return FormulaStructure(
            original_text=region_text,
            latex_expression=None,
            components=[],
        )
    
    # 1. 提取组件
    components: list[FormulaComponent] = []
    
    for char_info in chars:
        char_text = getattr(char_info, "char", "")
        if not char_text or char_text.isspace():
            continue
        
        # 判断组件类型
        comp_type = _classify_component(char_text)
        
        # 检测上下标（通过字体大小和位置）
        is_subscript = False
        is_superscript = False
        
        if len(chars) > 1:
            avg_size = sum(getattr(c, "font_size", 12) for c in chars) / len(chars)
            char_size = getattr(char_info, "font_size", 12)
            
            if char_size < avg_size * 0.8:
                # 字体较小，可能是下标
                y_center = (getattr(char_info, "y0", 0) + getattr(char_info, "y1", 0)) / 2
                # 简单启发式：如果 y 坐标低于平均值，可能是下标
                if y_center < sum((getattr(c, "y0", 0) + getattr(c, "y1", 0)) / 2 for c in chars) / len(chars):
                    is_subscript = True
                else:
                    is_superscript = True
        
        component = FormulaComponent(
            text=char_text,
            x0=getattr(char_info, "x0", 0),
            y0=getattr(char_info, "y0", 0),
            x1=getattr(char_info, "x1", 0),
            y1=getattr(char_info, "y1", 0),
            component_type=comp_type,
            font_name=getattr(char_info, "font_name", None),
            font_size=getattr(char_info, "font_size", None),
            is_subscript=is_subscript,
            is_superscript=is_superscript,
        )
        components.append(component)
    
    # 2. 检测特殊结构
    has_fractions = _detect_fractions(region_text, components)
    has_superscripts = any(c.is_superscript for c in components)
    has_subscripts = any(c.is_subscript for c in components)
    has_integrals = "∫" in region_text or "\\int" in region_text.lower()
    has_summations = "∑" in region_text or "\\sum" in region_text.lower()
    
    # 3. 尝试生成 LaTeX 表达式（简化版）
    latex_expr = _generate_latex_expression(region_text, components)
    
    return FormulaStructure(
        original_text=region_text,
        latex_expression=latex_expr,
        components=components,
        has_fractions=has_fractions,
        has_superscripts=has_superscripts,
        has_subscripts=has_subscripts,
        has_integrals=has_integrals,
        has_summations=has_summations,
    )


def _classify_component(char: str) -> str:
    """分类公式组件类型"""
    if char.isdigit():
        return "number"
    if char.isalpha():
        return "variable"
    
    # 运算符
    operators = "+-*/=<>≤≥≠≈±×÷"
    if char in operators:
        return "operator"
    
    # 函数符号
    functions = "sin cos tan log ln exp sqrt"
    if char.lower() in functions:
        return "function"
    
    # 数学符号
    symbols = "∑∏∫∂∇∞πθαβγδλμσφω"
    if char in symbols:
        return "symbol"
    
    return "symbol"


def _detect_fractions(text: str, components: list[FormulaComponent]) -> bool:
    """检测是否包含分数"""
    # 简单的分数检测：包含分数线或分数符号
    fraction_patterns = [
        r"/",
        r"\\frac",
        r"\\dfrac",
        r"⁄",  # Unicode 分数斜线
    ]
    
    for pattern in fraction_patterns:
        if re.search(pattern, text):
            return True
    
    # 检查是否有上下对齐的文本（可能是分数）
    if len(components) >= 3:
        # 简单启发式：如果有明显的上下结构
        y_coords = [c.y0 for c in components]
        if max(y_coords) - min(y_coords) > sum(c.font_size or 12 for c in components) / len(components) * 1.5:
            return True
    
    return False


def _generate_latex_expression(text: str, components: list[FormulaComponent]) -> str | None:
    """
    生成简化的 LaTeX 表达式
    
    这是一个简化实现，主要处理常见的数学符号转换
    """
    if not text:
        return None
    
    # 如果文本已经包含 LaTeX 语法，直接返回
    if "\\" in text or "$" in text:
        return text
    
    # 简单的符号替换
    symbol_map = {
        "∑": "\\sum",
        "∏": "\\prod",
        "∫": "\\int",
        "∂": "\\partial",
        "∇": "\\nabla",
        "∞": "\\infty",
        "π": "\\pi",
        "θ": "\\theta",
        "α": "\\alpha",
        "β": "\\beta",
        "γ": "\\gamma",
        "δ": "\\delta",
        "λ": "\\lambda",
        "μ": "\\mu",
        "σ": "\\sigma",
        "φ": "\\phi",
        "ω": "\\omega",
        "≤": "\\leq",
        "≥": "\\geq",
        "≠": "\\neq",
        "≈": "\\approx",
        "±": "\\pm",
        "×": "\\times",
        "÷": "\\div",
    }
    
    latex_text = text
    for symbol, latex in symbol_map.items():
        latex_text = latex_text.replace(symbol, latex)
    
    # 处理上下标（简化版）
    # 这里只是标记，真正的 LaTeX 生成需要更复杂的解析
    
    return latex_text if latex_text != text else None


def formula_structure_to_dict(structure: FormulaStructure) -> dict[str, Any]:
    """将公式结构转换为字典（用于 JSON 序列化）"""
    return {
        "original_text": structure.original_text,
        "latex_expression": structure.latex_expression,
        "components": [
            {
                "text": c.text,
                "x0": c.x0,
                "y0": c.y0,
                "x1": c.x1,
                "y1": c.y1,
                "component_type": c.component_type,
                "font_name": c.font_name,
                "font_size": c.font_size,
                "is_subscript": c.is_subscript,
                "is_superscript": c.is_superscript,
            }
            for c in structure.components
        ],
        "has_fractions": structure.has_fractions,
        "has_superscripts": structure.has_superscripts,
        "has_subscripts": structure.has_subscripts,
        "has_integrals": structure.has_integrals,
        "has_summations": structure.has_summations,
    }

