"""
高级布局处理增强模块

包括：
1. 基于文本相似度的跨页页眉/页脚检测
2. 智能脚注识别
3. 阅读顺序优化
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（改进版：使用序列相似度）

    Args:
        text1: 第一个文本
        text2: 第二个文本

    Returns:
        相似度分数（0.0-1.0）
    """
    if not text1 or not text2:
        return 0.0

    # 标准化文本
    def normalize(t: str) -> str:
        # 移除页码等变化部分
        t = re.sub(r"\d+", "", t.lower().strip())
        # 移除特殊字符，只保留字母和空格
        t = re.sub(r"[^\w\s]", "", t)
        return re.sub(r"\s+", " ", t)

    norm1 = normalize(text1)
    norm2 = normalize(text2)

    if not norm1 and not norm2:
        return 1.0

    # 计算字符级别的Jaccard相似度
    set1 = set(norm1)
    set2 = set(norm2)
    if not set1 and not set2:
        return 1.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)
    jaccard = intersection / max(union, 1.0)

    # 计算序列相似度（最长公共子序列比例）
    lcs_len = _longest_common_subsequence_length(norm1, norm2)
    max_len = max(len(norm1), len(norm2))
    lcs_similarity = lcs_len / max_len if max_len > 0 else 0.0

    # 综合相似度（加权平均）
    similarity = 0.6 * jaccard + 0.4 * lcs_similarity
    return similarity


def _longest_common_subsequence_length(s1: str, s2: str) -> int:
    """计算最长公共子序列长度（简化版）"""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]


def detect_repeated_headers_footers(pages: list[dict[str, Any]], similarity_threshold: float = 0.7) -> None:
    """
    检测并标记跨页重复的页眉/页脚（基于文本相似度）

    Args:
        pages: 页面列表（每个页面包含 blocks）
        similarity_threshold: 相似度阈值（默认 0.7）
    """
    # 收集所有页眉/页脚的文本
    header_counter: Counter[str] = Counter()
    footer_counter: Counter[str] = Counter()

    for page in pages:
        for block in page.get("blocks", []):
            role = block.get("is_header_footer")
            if not role:
                continue

            text = (block.get("text") or "").strip()
            if not text:
                continue

            if role == "header":
                header_counter[text] += 1
            elif role == "footer":
                footer_counter[text] += 1

    # 使用相似度分组页眉/页脚
    header_groups: dict[str, set[str]] = {}
    footer_groups: dict[str, set[str]] = {}

    # 分组页眉
    for text, count in header_counter.items():
        if count < 2:  # 至少出现2次才考虑为重复页眉
            continue

        grouped = False
        for group_key in list(header_groups.keys()):
            if calculate_text_similarity(text, group_key) >= similarity_threshold:
                header_groups[group_key].add(text)
                grouped = True
                break

        if not grouped:
            header_groups[text] = {text}

    # 分组页脚
    for text, count in footer_counter.items():
        if count < 2:  # 至少出现2次才考虑为重复页脚
            continue

        grouped = False
        for group_key in list(footer_groups.keys()):
            if calculate_text_similarity(text, group_key) >= similarity_threshold:
                footer_groups[group_key].add(text)
                grouped = True
                break

        if not grouped:
            footer_groups[text] = {text}

    # 合并所有相似文本
    header_keep = set()
    for group in header_groups.values():
        header_keep.update(group)

    footer_keep = set()
    for group in footer_groups.values():
        footer_keep.update(group)

    # 应用页眉/页脚过滤：只保留重复的页眉/页脚
    for page in pages:
        for block in page.get("blocks", []):
            role = block.get("is_header_footer")
            if not role:
                continue

            text = (block.get("text") or "").strip()
            if not text:
                continue

            if role == "header":
                # 检查是否与保留的页眉相似
                keep = any(
                    calculate_text_similarity(text, keep_text) >= similarity_threshold
                    for keep_text in header_keep
                )
                if not keep:
                    block["is_header_footer"] = None
            elif role == "footer":
                # 检查是否与保留的页脚相似
                keep = any(
                    calculate_text_similarity(text, keep_text) >= similarity_threshold
                    for keep_text in footer_keep
                )
                if not keep:
                    block["is_header_footer"] = None

    logger.info(
        f"检测到 {len(header_keep)} 个重复页眉组，{len(footer_keep)} 个重复页脚组"
    )


def enhance_footnote_detection(blocks: list[dict[str, Any]], page_height: float) -> None:
    """
    改进的脚注识别算法

    Args:
        blocks: 文本块列表
        page_height: 页面高度
    """
    footnote_patterns = [
        r"^\s*\d+[\).\]]\s+",  # "1) " 或 "1. " 或 "1] "
        r"^\s*\[\d+\]\s+",  # "[1] "
        r"^\s*[a-z]\d*[\).]\s+",  # "a) " 或 "a. "
        r"^\s*[*†‡§¶]+",  # "* " 或 "† " 或 "‡ "
        r"^\s*\^?\d+",  # "^1" 或 "1"
    ]

    for block in blocks:
        # 跳过已经标记为页眉/页脚的块
        if block.get("is_header_footer"):
            continue

        # 跳过已经是脚注的块
        if block.get("is_footnote"):
            continue

        bbox = block.get("bbox") or {}
        if not bbox:
            continue

        y0 = float(bbox.get("y0", 0))
        y1 = float(bbox.get("y1", 0))
        block_height = y1 - y0

        # 条件1：位于底部15%区域
        is_bottom = y0 >= 0.85 * page_height

        # 条件2：以脚注标记开头
        text_raw = (block.get("text") or "").strip()
        starts_with_marker = any(re.match(pattern, text_raw) for pattern in footnote_patterns)

        # 条件3：块高度较小（脚注通常较小）
        is_small_block = block_height < 0.025 * page_height  # 小于页面高度的2.5%

        # 条件4：文本长度适中
        text_len = len(text_raw)
        reasonable_length = 5 < text_len < 800  # 放宽长度限制

        # 条件5：字体大小通常较小（如果可用）
        font_size = block.get("font_size") or 0
        is_small_font = font_size > 0 and font_size < 10

        # 条件6：检查是否包含引用标记（如 "see", "ibid", "cf." 等）
        has_reference_markers = bool(
            re.search(
                r"\b(see|ibid|cf\.|ref\.|cfr\.|see also|et al\.)\b",
                text_raw,
                re.IGNORECASE,
            )
        )

        # 综合判断
        score = 0
        if is_bottom:
            score += 3
        if starts_with_marker:
            score += 4
        if is_small_block:
            score += 2
        if reasonable_length:
            score += 2
        if is_small_font:
            score += 1
        if has_reference_markers:
            score += 2

        # 总分达到阈值则标记为脚注
        if score >= 6:  # 需要至少6分才认为是脚注
            block["is_footnote"] = True
            block["footnote_confidence"] = min(score / 14.0, 1.0)  # 归一化置信度
        else:
            block.setdefault("is_footnote", False)


def optimize_reading_order(blocks: list[dict[str, Any]], page_width: float, page_height: float) -> None:
    """
    优化阅读顺序（改进版：支持多栏布局和复杂布局）

    Args:
        blocks: 文本块列表（会被重新排序）
        page_width: 页面宽度
        page_height: 页面高度
    """
    if not blocks:
        return

    # 按列->Y坐标->X坐标排序（改进版）
    def get_sort_key(block: dict[str, Any]) -> tuple[int, float, float]:
        bbox = block.get("bbox") or {}
        if not bbox:
            return (0, 0.0, 0.0)

        x0 = float(bbox.get("x0", 0))
        y0 = float(bbox.get("y0", 0))
        x1 = float(bbox.get("x1", 0))
        y1 = float(bbox.get("y1", 0))

        # 计算列索引（改进：考虑多栏布局）
        column_index = get_column_index_from_bbox(x0, x1, page_width)

        # Y坐标（从上到下）
        y_pos = y0

        # X坐标（从左到右，用于同列内的排序）
        x_pos = x0

        return (column_index, y_pos, x_pos)

    # 排序
    blocks.sort(key=get_sort_key)

    # 更新 reading_order
    for idx, block in enumerate(blocks):
        block["reading_order"] = idx


def get_column_index_from_bbox(x0: float, x1: float, page_width: float) -> int:
    """
    计算文本块所在的列索引（支持多栏布局）

    Args:
        x0: 块左边界
        x1: 块右边界
        page_width: 页面宽度

    Returns:
        列索引（0, 1, 2, ...）
    """
    # 块的X中心位置
    center_x = (x0 + x1) / 2

    # 单栏布局
    if page_width < 400:
        return 0

    # 两栏布局
    if page_width < 700:
        if center_x < page_width / 2:
            return 0
        else:
            return 1

    # 三栏或更多栏
    # 估算列数（假设每列宽度约为页面宽度的30-40%）
    column_width = page_width / 3.0
    column_index = int(center_x / column_width)
    return min(column_index, 2)  # 最多3栏


def enhance_layout_processing(
    pages: list[dict[str, Any]],
    enable_header_footer_detection: bool = True,
    enable_footnote_enhancement: bool = True,
    enable_reading_order_optimization: bool = True,
) -> None:
    """
    综合布局处理增强入口函数

    Args:
        pages: 页面列表
        enable_header_footer_detection: 是否启用页眉/页脚检测
        enable_footnote_enhancement: 是否启用脚注增强
        enable_reading_order_optimization: 是否启用阅读顺序优化
    """
    if enable_header_footer_detection:
        detect_repeated_headers_footers(pages)

    for page in pages:
        blocks = page.get("blocks", [])
        page_height = float(page.get("height", 0))

        if enable_footnote_enhancement and page_height > 0:
            enhance_footnote_detection(blocks, page_height)

        if enable_reading_order_optimization:
            page_width = float(page.get("width", 0))
            if page_width > 0:
                optimize_reading_order(blocks, page_width, page_height)

