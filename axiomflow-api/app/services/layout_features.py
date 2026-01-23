"""
布局检测特征工程模块

提取PDF结构特征、视觉特征、几何特征等多维度特征用于布局分类。
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """特征提取器：从PDF块中提取多维度特征"""

    def __init__(self):
        self.math_symbol_pattern = re.compile(
            r"[+\-*/=<>≤≥±×÷∑∏∫√∞∈∉⊂⊃∪∩⇒⇔∀∃∧∨¬]"
        )
        self.formula_pattern = re.compile(
            r"\$[^$]+\$|\\[a-zA-Z]+\{|[a-zA-Z]+\^[0-9]|_[0-9]|\\frac"
        )

    def extract_block_features(
        self, block: dict, page_width: float, page_height: float, all_blocks: list[dict]
    ) -> dict[str, Any]:
        """
        提取单个块的完整特征集。

        Args:
            block: PDF块字典
            page_width: 页面宽度
            page_height: 页面高度
            all_blocks: 当前页面所有块（用于上下文特征）

        Returns:
            特征字典
        """
        features = {}

        # 1. 文本特征
        text = (block.get("text") or "").strip()
        features.update(self._extract_text_features(text))

        # 2. 字体特征
        features.update(self._extract_font_features(block, all_blocks))

        # 3. 位置特征
        bbox = block.get("bbox") or {}
        if bbox:
            features.update(
                self._extract_position_features(bbox, page_width, page_height)
            )

        # 4. 几何特征
        features.update(self._extract_geometric_features(block, all_blocks))

        # 5. 内容特征
        features.update(self._extract_content_features(text))

        # 6. 上下文特征
        features.update(self._extract_context_features(block, all_blocks))

        return features

    def _extract_text_features(self, text: str) -> dict[str, Any]:
        """提取文本相关特征"""
        if not text:
            return {
                "text_length": 0,
                "text_density": 0.0,
                "line_count": 0,
                "word_count": 0,
                "char_density": 0.0,
            }

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        words = text.split()
        chars = [c for c in text if c.strip()]

        # 文本密度（每单位面积）
        text_length = len(text)
        area = len(lines) * max((len(line) for line in lines), default=1)
        text_density = text_length / max(area, 1.0)

        return {
            "text_length": text_length,
            "text_density": text_density,
            "line_count": len(lines),
            "word_count": len(words),
            "char_density": len(chars) / max(text_length, 1.0),
        }

    def _extract_font_features(
        self, block: dict, all_blocks: list[dict]
    ) -> dict[str, Any]:
        """提取字体相关特征"""
        font_dict = block.get("font") or {}
        font_size = font_dict.get("size", 0.0)
        font_name = font_dict.get("name", "").lower()

        # 计算平均字体大小（用于归一化）
        all_font_sizes = []
        for b in all_blocks:
            b_font = b.get("font") or {}
            if b_font.get("size", 0) > 0:
                all_font_sizes.append(b_font.get("size", 0))

        avg_font_size = sum(all_font_sizes) / max(len(all_font_sizes), 1.0)
        median_font_size = sorted(all_font_sizes)[len(all_font_sizes) // 2] if all_font_sizes else 1.0

        # 字体大小比率
        font_size_ratio = font_size / max(avg_font_size, 1.0)
        font_size_median_ratio = font_size / max(median_font_size, 1.0)

        # 字体样式推断（基于名称）
        is_bold = any(keyword in font_name for keyword in ["bold", "heavy", "black"])
        is_italic = any(keyword in font_name for keyword in ["italic", "oblique"])
        is_math_font = any(
            keyword in font_name
            for keyword in ["math", "cm", "mt", "tex", "mono", "sym", "ital"]
        )
        is_cjk = any(
            keyword in font_name for keyword in ["cjk", "han", "chinese", "jp", "kr"]
        )

        # 字体大小层次（相对于所有字体）
        if all_font_sizes:
            sorted_sizes = sorted(set(all_font_sizes), reverse=True)
            size_rank = sorted_sizes.index(font_size) if font_size in sorted_sizes else -1
            total_ranks = len(sorted_sizes)
            size_hierarchy = 1.0 - (size_rank / max(total_ranks, 1.0))
        else:
            size_hierarchy = 0.5

        return {
            "font_size": font_size,
            "font_size_ratio": font_size_ratio,
            "font_size_median_ratio": font_size_median_ratio,
            "font_size_hierarchy": size_hierarchy,
            "is_bold": 1 if is_bold else 0,
            "is_italic": 1 if is_italic else 0,
            "is_math_font": 1 if is_math_font else 0,
            "is_cjk_font": 1 if is_cjk else 0,
        }

    def _extract_position_features(
        self, bbox: dict, page_width: float, page_height: float
    ) -> dict[str, Any]:
        """提取位置相关特征"""
        x0, y0, x1, y1 = (
            float(bbox.get("x0", 0)),
            float(bbox.get("y0", 0)),
            float(bbox.get("x1", 0)),
            float(bbox.get("y1", 0)),
        )

        width = x1 - x0
        height = y1 - y0
        area = width * height

        # 相对位置（归一化到0-1）
        x_center = (x0 + x1) / 2.0
        y_center = (y0 + y1) / 2.0
        x_position = x_center / max(page_width, 1.0)
        y_position = y_center / max(page_height, 1.0)

        # 相对大小
        relative_width = width / max(page_width, 1.0)
        relative_height = height / max(page_height, 1.0)
        relative_area = area / max(page_width * page_height, 1.0)

        # 宽高比
        aspect_ratio = width / max(height, 1.0)

        # 页面位置区域（上/中/下，左/中/右）
        page_region_y = 0 if y_position < 0.33 else (1 if y_position > 0.67 else 2)
        page_region_x = 0 if x_position < 0.33 else (1 if x_position > 0.67 else 2)

        return {
            "x_position": x_position,
            "y_position": y_position,
            "relative_width": relative_width,
            "relative_height": relative_height,
            "relative_area": relative_area,
            "aspect_ratio": aspect_ratio,
            "page_region_x": page_region_x,
            "page_region_y": page_region_y,
        }

    def _extract_geometric_features(
        self, block: dict, all_blocks: list[dict]
    ) -> dict[str, Any]:
        """提取几何特征（对齐、间距等）"""
        bbox = block.get("bbox") or {}
        if not bbox:
            return {
                "alignment_score": 0.0,
                "spacing_score": 0.0,
                "column_consistency": 0.0,
            }

        x0, y0, x1, y1 = (
            float(bbox.get("x0", 0)),
            float(bbox.get("y0", 0)),
            float(bbox.get("x1", 0)),
            float(bbox.get("y1", 0)),
        )

        # 对齐分数（与其他块的水平对齐程度）
        alignment_score = 0.0
        nearby_blocks = [
            b
            for b in all_blocks
            if b != block and (b.get("bbox") or {}).get("page") == bbox.get("page")
        ]

        if nearby_blocks:
            x0_values = [
                float((b.get("bbox") or {}).get("x0", 0))
                for b in nearby_blocks
                if b.get("bbox")
            ]
            if x0_values:
                avg_x0 = sum(x0_values) / len(x0_values)
                # 对齐分数：x0接近平均值的程度
                diff = abs(x0 - avg_x0)
                max_diff = max(x0_values) - min(x0_values) if len(x0_values) > 1 else 1.0
                alignment_score = 1.0 - min(diff / max(max_diff, 1.0), 1.0)

        # 间距分数（与相邻块的间距合理性）
        spacing_score = 0.0
        # 找到垂直方向上最近的块
        vertical_blocks = [
            b
            for b in nearby_blocks
            if b.get("bbox")
            and abs(float((b.get("bbox") or {}).get("x0", 0)) - x0) < 50  # 同列
        ]
        if vertical_blocks:
            gaps = []
            for b in vertical_blocks:
                b_bbox = b.get("bbox") or {}
                b_y1 = float(b_bbox.get("y1", 0))
                gap = abs(y0 - b_y1)
                if gap < 100:  # 只考虑附近的块
                    gaps.append(gap)

            if gaps:
                avg_gap = sum(gaps) / len(gaps)
                # 间距越一致，分数越高
                gap_variance = sum((g - avg_gap) ** 2 for g in gaps) / len(gaps)
                spacing_score = 1.0 / (1.0 + gap_variance / 100.0)

        # 列一致性（在同一列的块占比）
        column_index = block.get("column_index", 0)
        same_column_count = sum(
            1
            for b in nearby_blocks
            if b.get("column_index") == column_index
        )
        column_consistency = same_column_count / max(len(nearby_blocks), 1.0)

        return {
            "alignment_score": alignment_score,
            "spacing_score": spacing_score,
            "column_consistency": column_consistency,
        }

    def _extract_content_features(self, text: str) -> dict[str, Any]:
        """提取内容特征（数字、符号、模式等）"""
        if not text:
            return {
                "has_numbers": 0,
                "has_math_symbols": 0,
                "has_latex": 0,
                "math_symbol_density": 0.0,
                "non_alnum_ratio": 0.0,
                "starts_with_caption": 0,
                "is_short_line": 0,
            }

        # 数字检测
        has_numbers = 1 if re.search(r"\d", text) else 0

        # 数学符号检测
        math_symbols = len(self.math_symbol_pattern.findall(text))
        has_math_symbols = 1 if math_symbols > 0 else 0
        math_symbol_density = math_symbols / max(len(text), 1.0)

        # LaTeX模式检测
        has_latex = 1 if self.formula_pattern.search(text) else 0

        # 非字母数字字符比例
        alnum_count = sum(1 for c in text if c.isalnum())
        non_alnum_ratio = 1.0 - (alnum_count / max(len(text), 1.0))

        # 图表标题模式
        text_lower = text.lower().strip()
        starts_with_caption = (
            1
            if text_lower.startswith(("figure", "fig.", "table", "fig ", "fig:"))
            else 0
        )

        # 短行检测（可能是标题或公式）
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        is_short_line = 1 if len(lines) <= 2 and len(text) < 100 else 0

        return {
            "has_numbers": has_numbers,
            "has_math_symbols": has_math_symbols,
            "has_latex": has_latex,
            "math_symbol_density": math_symbol_density,
            "non_alnum_ratio": non_alnum_ratio,
            "starts_with_caption": starts_with_caption,
            "is_short_line": is_short_line,
        }

    def _extract_context_features(
        self, block: dict, all_blocks: list[dict]
    ) -> dict[str, Any]:
        """提取上下文特征（周围块的特征）"""
        bbox = block.get("bbox") or {}
        if not bbox:
            return {
                "nearby_block_count": 0,
                "above_block_type": 0,
                "below_block_type": 0,
            }

        page_index = bbox.get("page", 0)
        x0, y0, x1, y1 = (
            float(bbox.get("x0", 0)),
            float(bbox.get("y0", 0)),
            float(bbox.get("x1", 0)),
            float(bbox.get("y1", 0)),
        )

        # 附近的块
        nearby_blocks = [
            b
            for b in all_blocks
            if b != block
            and (b.get("bbox") or {}).get("page") == page_index
            and self._blocks_nearby(bbox, b.get("bbox") or {}, threshold=50)
        ]

        nearby_block_count = len(nearby_blocks)

        # 上方和下方的块类型
        above_blocks = [
            b
            for b in nearby_blocks
            if (b.get("bbox") or {}).get("y1", 0) < y0
        ]
        below_blocks = [
            b
            for b in nearby_blocks
            if (b.get("bbox") or {}).get("y0", 0) > y1
        ]

        # 块类型编码（简单映射）
        type_map = {"heading": 1, "paragraph": 2, "caption": 3, "formula": 4, "figure": 5, "table": 6}
        
        above_block_type = 0
        if above_blocks:
            above_type = above_blocks[-1].get("type", "paragraph")
            above_block_type = type_map.get(above_type, 0)

        below_block_type = 0
        if below_blocks:
            below_type = below_blocks[0].get("type", "paragraph")
            below_block_type = type_map.get(below_type, 0)

        return {
            "nearby_block_count": nearby_block_count,
            "above_block_type": above_block_type,
            "below_block_type": below_block_type,
        }

    def _blocks_nearby(self, bbox1: dict, bbox2: dict, threshold: float = 50.0) -> bool:
        """判断两个块是否相邻"""
        x1_0, y1_0 = float(bbox1.get("x0", 0)), float(bbox1.get("y0", 0))
        x1_1, y1_1 = float(bbox1.get("x1", 0)), float(bbox1.get("y1", 0))
        x2_0, y2_0 = float(bbox2.get("x0", 0)), float(bbox2.get("y0", 0))
        x2_1, y2_1 = float(bbox2.get("x1", 0)), float(bbox2.get("y1", 0))

        # 计算中心距离
        center1_x = (x1_0 + x1_1) / 2.0
        center1_y = (y1_0 + y1_1) / 2.0
        center2_x = (x2_0 + x2_1) / 2.0
        center2_y = (y2_0 + y2_1) / 2.0

        distance = (
            (center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2
        ) ** 0.5

        return distance < threshold

