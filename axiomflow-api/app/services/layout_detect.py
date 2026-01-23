from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .formula_detect import detect_formula_block, FontInfo

logger = logging.getLogger(__name__)


RegionType = Literal["figure", "table", "formula", "unknown"]


@dataclass(frozen=True)
class Region:
    type: RegionType
    x0: float
    y0: float
    x1: float
    y1: float
    score: float = 0.5


def _bbox_intersect(a: dict, b: Region) -> bool:
    ax0, ay0, ax1, ay1 = a["x0"], a["y0"], a["x1"], a["y1"]
    bx0, by0, bx1, by1 = b.x0, b.y0, b.x1, b.y1
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    return (ix1 - ix0) > 0 and (iy1 - iy0) > 0


def detect_regions_heuristic(blocks: list[dict]) -> list[Region]:
    """
    v0.6 改进的版面检测（启发式 + vfont 字体匹配）：
    - 公式：结合字体名称匹配（vfont）和符号密度检测
    - 图/表：从 caption（Figure/Table 开头）推断其上方区域为 figure/table
    """
    regions: list[Region] = []

    # 1) Formula-like blocks（改进版：支持 vfont 字体匹配）
    for blk in blocks:
        text = (blk.get("text") or "").strip()
        if not text:
            continue
        bbox = blk.get("bbox") or {}
        if not bbox:
            continue

        # 提取字体信息
        font_info = None
        font_dict = blk.get("font")
        if font_dict:
            font_info = FontInfo(
                name=font_dict.get("name", ""),
                size=font_dict.get("size"),
            )

        # 使用改进的公式检测（支持 vfont）
        if detect_formula_block(blk, font_info=font_info):
            # 获取置信度（如果已计算）
            confidence = blk.get("formula_confidence", 0.7)
            
            regions.append(
                Region(
                    type="formula",
                    x0=float(bbox["x0"]),
                    y0=float(bbox["y0"]),
                    x1=float(bbox["x1"]),
                    y1=float(bbox["y1"]),
                    score=float(confidence),
                )
            )

    # 2) Figure/Table inferred from caption
    for i, blk in enumerate(blocks):
        if blk.get("type") != "caption":
            continue
        text = (blk.get("text") or "").strip().lower()
        bbox = blk.get("bbox") or {}
        if not bbox:
            continue

        if text.startswith(("figure ", "fig. ")):
            region_type: RegionType = "figure"
        elif text.startswith(("table ",)):
            region_type = "table"
        else:
            continue

        # 简单推断：caption 上方一段区域（同列附近）属于 figure/table
        # 先向上找 1~3 个块，取他们的 bbox union
        x0, y0, x1, y1 = float(bbox["x0"]), float(bbox["y0"]), float(bbox["x1"]), float(bbox["y1"])
        for j in range(max(0, i - 3), i):
            up = blocks[j]
            upb = up.get("bbox") or {}
            if not upb:
                continue
            # 只取在 caption 上方的块
            if float(upb["y1"]) <= float(bbox["y0"]) + 2:
                x0 = min(x0, float(upb["x0"]))
                y0 = min(y0, float(upb["y0"]))
                x1 = max(x1, float(upb["x1"]))
                y1 = max(y1, float(upb["y1"]))

        regions.append(Region(type=region_type, x0=x0, y0=y0, x1=x1, y1=y1, score=0.55))

    return regions


def apply_regions_to_blocks(blocks: list[dict], regions: list[Region]) -> None:
    """
    将 regions 融合到 blocks：若 block bbox 与 region 相交，且当前类型较弱，则提升 block.type。
    """
    priority = {"heading": 1, "paragraph": 1, "caption": 2, "formula": 3, "figure": 3, "table": 3}
    for blk in blocks:
        bbox = blk.get("bbox") or {}
        if not bbox:
            continue
        best: Region | None = None
        for r in regions:
            if _bbox_intersect(bbox, r):
                if best is None or r.score > best.score:
                    best = r
        if not best:
            continue

        cur = blk.get("type") or "paragraph"
        if best.type in ("figure", "table", "formula"):
            if priority.get(best.type, 0) >= priority.get(cur, 0):
                blk["type"] = best.type


def detect_regions_feature_based(
    blocks: list[dict],
    page_width: float,
    page_height: float,
    model_path: Path | None = None,
    use_ml: bool = True,
    min_confidence: float = 0.4,
) -> list[Region]:
    """
    基于特征工程的布局检测（与开源项目不同的方案）

    使用PDF结构特征 + 轻量ML分类器进行布局检测，而非纯视觉检测。

    Args:
        blocks: PDF块列表
        page_width: 页面宽度
        page_height: 页面高度
        model_path: 预训练模型路径（可选）
        use_ml: 是否使用ML分类器（False时使用规则回退）
        min_confidence: 最小置信度阈值

    Returns:
        检测到的区域列表

    与开源项目的差异：
    - 开源：纯视觉检测（YOLO ONNX模型）
    - 本方法：PDF结构 + 特征工程 + 轻量ML分类器

    优势：
    - 充分利用PDF原生信息
    - CPU性能优秀
    - 可解释性强
    - 无需深度学习依赖
    """
    try:
        from .feature_based_layout_detect import detect_regions_feature_based as _detect

        return _detect(
            blocks,
            page_width,
            page_height,
            model_path=model_path,
            use_ml=use_ml,
            min_confidence=min_confidence,
        )
    except ImportError as e:
        logger.warning(
            f"无法导入特征检测器，回退到启发式方法: {e}"
        )
        return detect_regions_heuristic(blocks)


