from __future__ import annotations

"""
文档结构分析模块

目标：
- 基于 heading/paragraph 等块类型，自动推断章节层级（chapter/section/subsection 等）
- 为每个块打上 section_id、section_level、section_title 等元数据
- 生成全局 outline 结构，供导出/翻译使用（如生成目录、按章节翻译）
"""

from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class SectionNode:
    """文档章节节点"""

    id: str
    title: str
    level: int
    page_index: int
    start_block_id: str
    end_block_id: Optional[str] = None
    children: List["SectionNode"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "level": self.level,
            "page_index": self.page_index,
            "start_block_id": self.start_block_id,
            "end_block_id": self.end_block_id,
            "children": [c.to_dict() for c in self.children],
        }


_HEADING_NUMBER_PATTERN = re.compile(
    r"""
    ^\s*
    (?:                # 常见编号模式：
        (?:第?\s*\d+[\.\-、]\s*)   |   # 第1. / 1. / 1- / 1、 等
        (?:[IVXLC]+\.)\s*         |   # 罗马数字 I. II. III.
        (?:[A-Z]\.)\s*                # A. B. C.
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _guess_heading_level(text: str, font_size: float | None, page_index: int) -> int:
    """
    基于编号模式 + 字号 + 文本特征推断标题层级：
    - 返回 1 表示最高级章节（如 Chapter / 一级标题）
    - 返回 2/3/... 表示子级
    - 返回 0 表示不认为是章节标题（普通 heading）
    """
    stripped = text.strip()
    if not stripped:
        return 0

    # 顶部标题（例如论文标题）倾向于 level 1
    if page_index == 0 and len(stripped) < 80:
        # 如果存在明显的大写或关键字
        if any(k in stripped.lower() for k in ["abstract", "introduction", "绪论", "引言", "目录"]):
            return 1

    # 检测编号模式
    m = _HEADING_NUMBER_PATTERN.match(stripped)
    if m:
        prefix = m.group(0)
        # 根据编号复杂度简单推断层级
        # 例如 "1." / "第1章" -> 1 级；"1.1" / "1-1" -> 2 级；"1.1.1" -> 3 级
        digits = re.findall(r"\d+", prefix)
        if len(digits) == 1:
            return 1
        if len(digits) == 2:
            return 2
        if len(digits) >= 3:
            return 3

    # 根据字号大致推断（相对于正文）
    if font_size is not None:
        if font_size >= 16:
            return 1
        if font_size >= 13:
            return 2
        if font_size >= 11:
            return 3

    # 短行 + 全大写/标题感，也认为是较高层级
    lines = [ln for ln in stripped.splitlines() if ln.strip()]
    if len(lines) <= 2 and len(stripped) < 60:
        letters = [ch for ch in stripped if ch.isalpha()]
        if letters:
            upper_ratio = sum(ch.isupper() for ch in letters) / max(len(letters), 1)
            if upper_ratio > 0.6:
                return 2

    return 0


def analyze_document_structure(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析整个文档的章节结构。

    产出：
    - sections: SectionNode 的树形结构（序列化为 list[dict]）
    - 为每个 block 添加：
        - section_id: 所属章节ID（无则为 None）
        - section_level: 所属章节层级（0 表示未归属到章节）
    """
    if not pages:
        return {"sections": []}

    # 扫描所有 heading 块，按阅读顺序构建线性列表
    heading_candidates: List[Dict[str, Any]] = []
    for page in pages:
        page_idx = int(page.get("index", 0))
        for blk in page.get("blocks", []):
            if blk.get("type") != "heading":
                continue
            text = (blk.get("text") or "").strip()
            if not text:
                continue
            font_size = None
            font = blk.get("font") or {}
            if "size" in font:
                try:
                    font_size = float(font["size"])
                except Exception:
                    font_size = None

            level = _guess_heading_level(text, font_size, page_idx)
            if level <= 0:
                continue

            heading_candidates.append(
                {
                    "block": blk,
                    "page_index": page_idx,
                    "level": level,
                    "text": text,
                }
            )

    if not heading_candidates:
        logger.info("未检测到章节标题，跳过文档结构分析")
        return {"sections": []}

    # 根据阅读顺序排序（page_index, reading_order）
    heading_candidates.sort(
        key=lambda h: (
            int(h["page_index"]),
            int(h["block"].get("reading_order", 0)),
        )
    )

    # 构建章节树（简单的层级堆栈算法）
    sections: List[SectionNode] = []
    stack: List[SectionNode] = []

    for idx, h in enumerate(heading_candidates):
        blk = h["block"]
        level = int(h["level"])
        page_index = int(h["page_index"])
        text = h["text"]
        sec_id = blk.get("id") or f"sec_{idx}"

        node = SectionNode(
            id=sec_id,
            title=text,
            level=level,
            page_index=page_index,
            start_block_id=blk.get("id", ""),
        )

        # 调整栈：确保栈顶的 level < 当前 level
        while stack and stack[-1].level >= level:
            finished = stack.pop()
            # 结束块 ID 先留空，稍后整体填充
            _ = finished

        if stack:
            # 当前 node 作为上一个更高层级的子节点
            stack[-1].children.append(node)
        else:
            sections.append(node)

        stack.append(node)

    # 计算每个章节的 end_block_id：下一个同级/更高层级章节开始之前的最后一个块
    # 首先构建块的全局线性序列
    linear_blocks: List[Dict[str, Any]] = []
    for page in pages:
        page_idx = int(page.get("index", 0))
        for blk in sorted(
            page.get("blocks", []),
            key=lambda b: int(b.get("reading_order", 0)),
        ):
            linear_blocks.append({"page_index": page_idx, "block": blk})

    # 为每个 block 预留 section_id/level 字段
    for item in linear_blocks:
        blk = item["block"]
        blk.setdefault("section_id", None)
        blk.setdefault("section_level", 0)

    # 展平章节列表（前序遍历）
    flat_sections: List[SectionNode] = []

    def _dfs(node: SectionNode) -> None:
        flat_sections.append(node)
        for c in node.children:
            _dfs(c)

    for root in sections:
        _dfs(root)

    # 为每个章节找到起止范围，并标注 blocks 的 section_id / section_level
    sec_index = {s.start_block_id: s for s in flat_sections}

    # 找到每个章节在 linear_blocks 中的起始索引
    start_indices: Dict[str, int] = {}
    for i, item in enumerate(linear_blocks):
        blk = item["block"]
        bid = blk.get("id")
        if bid in sec_index and bid not in start_indices:
            start_indices[bid] = i

    # 根据 start_indices 与章节顺序推断 end_block_id
    sorted_sec = [
        (s, start_indices.get(s.start_block_id, -1))
        for s in flat_sections
        if s.start_block_id in start_indices
    ]
    # 按起始索引排序
    sorted_sec.sort(key=lambda t: t[1])

    for idx, (sec, start_idx) in enumerate(sorted_sec):
        if start_idx < 0:
            continue
        # 结束位置：下一个章节开始前一块，或文档末尾
        if idx + 1 < len(sorted_sec):
            next_start = sorted_sec[idx + 1][1]
            end_idx = max(start_idx, next_start - 1)
        else:
            end_idx = len(linear_blocks) - 1

        # 写入 end_block_id
        if 0 <= end_idx < len(linear_blocks):
            sec.end_block_id = linear_blocks[end_idx]["block"].get("id")

        # 为范围内的所有块标注 section 信息
        for i in range(start_idx, end_idx + 1):
            blk = linear_blocks[i]["block"]
            blk["section_id"] = sec.id
            blk["section_level"] = sec.level

    logger.info(f"文档结构分析完成，检测到 {len(flat_sections)} 个章节节点")

    return {
        "sections": [s.to_dict() for s in sections],
    }


