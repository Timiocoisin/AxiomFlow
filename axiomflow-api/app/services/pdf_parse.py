from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal, Callable, Optional
from collections import Counter
import re

import fitz  # PyMuPDF

from ..core.ids import new_id
from .layout_detect import (
    detect_regions_heuristic,
    detect_regions_feature_based,
    apply_regions_to_blocks,
)
from .formula_detect import extract_fonts_from_text_dict, detect_formula_block, FontInfo
from .document_structure import analyze_document_structure


def _guess_block_type(text: str) -> Literal["heading", "caption", "paragraph"]:
    stripped = text.strip()
    # 图表标题
    lower = stripped.lower()
    if lower.startswith(("figure ", "fig. ", "table ")):
        return "caption"
    # 行数少、长度短的视为标题候选
    lines = [ln for ln in stripped.splitlines() if ln.strip()]
    if len(lines) <= 2 and len(stripped) <= 80:
        # 大写比例高或首字母大写较多，视为标题
        letters = [ch for ch in stripped if ch.isalpha()]
        if letters:
            upper_ratio = sum(ch.isupper() for ch in letters) / len(letters)
            if upper_ratio > 0.5:
                return "heading"
        if stripped.endswith((".", ":")) is False:
            return "heading"
    return "paragraph"


def _guess_column_index(x0: float, page_width: float) -> int:
    # 简单 2 栏/3 栏启发式：按相对位置切分
    ratio = x0 / max(page_width, 1.0)
    if ratio < 0.33:
        return 0
    if ratio < 0.66:
        return 1
    return 2


def _is_header_or_footer(y0: float, y1: float, page_height: float) -> str | None:
    # 简单按页面上下边界百分比判断（后续可做跨页重复文本检测）
    top = 0.08 * page_height
    bottom = 0.92 * page_height
    if y1 <= top:
        return "header"
    if y0 >= bottom:
        return "footer"
    return None


def _merge_paragraph_blocks(blocks: list[dict], *, page_height: float) -> list[dict]:
    """
    v0.3：段落合并（同页、同列、同类型 paragraph，且垂直间距小）
    """
    if not blocks:
        return blocks

    # 先按列、再按 y0 排序
    blocks_sorted = sorted(
        blocks,
        key=lambda b: (
            int(b.get("column_index", 0)),
            float((b.get("bbox") or {}).get("y0", 0.0)),
            float((b.get("bbox") or {}).get("x0", 0.0)),
        ),
    )

    merged: list[dict] = []
    gap_thresh = max(6.0, page_height * 0.012)  # 经验阈值

    for b in blocks_sorted:
        if not merged:
            merged.append(b)
            continue
        prev = merged[-1]
        if (
            (prev.get("type") == "paragraph")
            and (b.get("type") == "paragraph")
            and (prev.get("column_index") == b.get("column_index"))
            and (prev.get("page_index") == b.get("page_index"))
            and not prev.get("is_header_footer")
            and not b.get("is_header_footer")
        ):
            pb = prev.get("bbox") or {}
            cb = b.get("bbox") or {}
            if pb and cb:
                # 垂直间距
                gap = float(cb["y0"]) - float(pb["y1"])
                # 横向重叠（同列同段落）
                overlap = min(float(cb["x1"]), float(pb["x1"])) - max(float(cb["x0"]), float(pb["x0"]))
                if gap >= -2 and gap <= gap_thresh and overlap > 10:
                    # 合并 bbox
                    prev["bbox"]["x0"] = min(float(pb["x0"]), float(cb["x0"]))
                    prev["bbox"]["y0"] = min(float(pb["y0"]), float(cb["y0"]))
                    prev["bbox"]["x1"] = max(float(pb["x1"]), float(cb["x1"]))
                    prev["bbox"]["y1"] = max(float(pb["y1"]), float(cb["y1"]))
                    # 合并文本（保留换行）
                    prev["text"] = (prev.get("text") or "").rstrip() + "\n" + (b.get("text") or "").lstrip()
                    continue
        merged.append(b)

    return merged


def _extract_original_filename(pdf_path: Path) -> str:
    """从文件路径中提取原始文件名（去掉 document_id__ 前缀）"""
    filename = pdf_path.name
    if "__" in filename:
        # 格式: doc_xxx__filename.pdf -> filename.pdf
        filename = filename.split("__", 1)[1]
    return filename


def parse_pdf_to_structured_json(
    pdf_path: Path,
    *,
    document_id: str,
    project_id: str,
    lang_in: str,
    lang_out: str,
    use_hybrid_parser: bool = True,
    use_feature_based_layout: bool = True,
    # OCR 已完全移除，以下参数仅为兼容旧调用保留（不再生效）
    enable_ocr: bool = False,
    ocr_engine: str = "auto",
    vfont: str = "",
    vchar: str = "",
    use_cache: bool = True,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> dict:
    """
    解析 PDF 为结构化 JSON（文本 PDF 路线）：
    - 使用 PyMuPDF 提取每页 text blocks（含 bbox）；
    - 粗粒度推断 Block.type（heading/paragraph/caption）；
    - 估计列索引 column_index，后续可用于阅读顺序与布局增强。
    - 支持解析结果缓存（基于文件哈希）
    
    Args:
        pdf_path: PDF文件路径
        document_id: 文档ID
        project_id: 项目ID
        lang_in: 源语言
        lang_out: 目标语言
        use_hybrid_parser: 是否使用混合解析器（PyMuPDF + PDFMiner）
        vfont: 公式字体匹配正则表达式
        vchar: 公式字符匹配正则表达式
        use_cache: 是否使用缓存
    
    Returns:
        结构化文档JSON
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 尝试从缓存获取（仅基于文本解析参数，不再区分 OCR）
    if use_cache:
        try:
            from .pdf_cache import get_pdf_parse_cache

            cache = get_pdf_parse_cache()
            cached_result = cache.get(
                pdf_path,
                use_hybrid_parser=use_hybrid_parser,
                use_feature_based_layout=use_feature_based_layout,
                vfont=vfont,
                vchar=vchar,
            )
            if cached_result is not None:
                logger.info(f"从缓存加载PDF解析结果: {pdf_path.name}")
                # 更新document_id和project_id（可能不同）
                cached_result["document_id"] = document_id
                cached_result["project_id"] = project_id
                cached_result["lang_in"] = lang_in
                cached_result["lang_out"] = lang_out
                return cached_result
        except Exception as e:
            logger.warning(f"缓存查询失败，继续正常解析: {e}")
    
    # 如果启用混合解析，使用HybridPDFParser
    if use_hybrid_parser:
        try:
            from .hybrid_parser import parse_pdf_hybrid
            
            return parse_pdf_hybrid(
                pdf_path,
                document_id=document_id,
                project_id=project_id,
                lang_in=lang_in,
                lang_out=lang_out,
                use_deep_parsing=True,
                progress_callback=progress_callback,
            )
        except Exception as e:
            logger.warning(f"混合解析失败，回退到PyMuPDF: {e}", exc_info=True)
            # 继续使用原始PyMuPDF解析（use_hybrid_parser=False避免递归）
            return parse_pdf_to_structured_json(
                pdf_path,
                document_id=document_id,
                project_id=project_id,
                lang_in=lang_in,
                lang_out=lang_out,
                use_hybrid_parser=False,
                progress_callback=progress_callback,
            )
    now = datetime.utcnow().isoformat()
    doc = fitz.open(pdf_path.as_posix())
    total_pages = doc.page_count
    
    # 如果有进度回调，先通知总页数
    if progress_callback:
        progress_callback(0, total_pages, {"substage": "extract", "step_done": 0, "step_total": 1, "message": f"开始解析: {total_pages} 页"})
    
    pages = []
    reading_order = 0

    for page_index in range(total_pages):
        if progress_callback:
            progress_callback(page_index + 1, total_pages, {"substage": "extract", "step_done": 0, "step_total": 1, "message": f"读取页面: {page_index + 1}/{total_pages}"})
        page = doc.load_page(page_index)
        rect = page.rect

        # 提取字体信息（使用 dict 格式获取详细字体信息）
        if progress_callback:
            progress_callback(page_index + 1, total_pages, {"substage": "extract", "step_done": 0, "step_total": 1, "message": "提取文本与字体信息"})
        text_dict = page.get_text("dict")
        font_map = extract_fonts_from_text_dict(text_dict)

        blocks = []
        # (x0, y0, x1, y1, "text", block_no, block_type)
        block_dict_items = page.get_text("blocks")
        text_block_counter = 0  # 只计数有文本的块
        if progress_callback:
            progress_callback(
                page_index + 1,
                total_pages,
                {"substage": "extract", "step_done": 0, "step_total": len(block_dict_items) or 1, "message": f"解析文本块: 0/{len(block_dict_items) or 1}"},
            )
        
        for i, b in enumerate(block_dict_items):
            x0, y0, x1, y1, raw_text = b[0], b[1], b[2], b[3], b[4]
            text = (raw_text or "").strip()
            if not text:
                continue
            block_id = new_id("blk")
            block_type = _guess_block_type(text)
            column_index = _guess_column_index(x0, rect.width)
            hf = _is_header_or_footer(y0, y1, rect.height)

            # 获取该 block 的字体信息（font_map 只包含文本块）
            font_info = font_map.get(text_block_counter)
            text_block_counter += 1

            block_dict = {
                "id": block_id,
                "document_id": document_id,
                "type": block_type,
                "bbox": {
                    "page": page_index,
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                },
                # 临时 reading_order，后面会重排
                "reading_order": reading_order,
                "column_index": column_index,
                "page_index": page_index,
                "is_header_footer": hf,  # "header"|"footer"|None
                "text": text,
                "translation": None,
                "edited": False,
                "edited_at": None,
            }

            # 保存字体信息到 block（用于公式检测）
            if font_info:
                block_dict["font"] = {
                    "name": font_info.name,
                    "size": font_info.size,
                }

            blocks.append(block_dict)
            reading_order += 1
            # 页内更细的进度：每 20 个块通知一次（避免 WS 过载）
            if progress_callback and (i % 20 == 0):
                progress_callback(
                    page_index + 1,
                    total_pages,
                    {"substage": "extract", "step_done": i, "step_total": len(block_dict_items) or 1, "message": f"解析文本块: {i}/{len(block_dict_items) or 1}"},
                )

        # v0.7: layout regions (特征工程 + 轻量ML分类器)
        # 优先使用基于特征的检测器（与开源项目不同的方案）
        if use_feature_based_layout:
            try:
                if progress_callback:
                    progress_callback(page_index + 1, total_pages, {"substage": "layout", "step_done": 0, "step_total": 1, "message": "布局检测"})
                regions = detect_regions_feature_based(
                    blocks,
                    page_width=float(rect.width),
                    page_height=float(rect.height),
                    use_ml=True,
                    min_confidence=0.4,
                )
            except Exception as e:
                logger.warning(
                    f"特征检测失败，回退到启发式方法: {e}",
                    exc_info=True,
                )
                regions = detect_regions_heuristic(blocks)
        else:
            # 使用传统启发式方法
            regions = detect_regions_heuristic(blocks)
        
        apply_regions_to_blocks(blocks, regions)

        # v0.3: 过滤页眉页脚（先标记，再在翻译/导出阶段可选择跳过）
        # v0.3: 段落合并（提高翻译质量与一致性）
        blocks = _merge_paragraph_blocks(blocks, page_height=float(rect.height))

        # v0.3: 阅读顺序重排（使用增强模块优化）
        try:
            from .layout_enhancement import optimize_reading_order
            if progress_callback:
                progress_callback(page_index + 1, total_pages, {"substage": "order", "step_done": 0, "step_total": 1, "message": "优化阅读顺序"})

            optimize_reading_order(blocks, float(rect.width), float(rect.height))
            # 更新全局 reading_order
            for b in blocks:
                local_order = b.get("reading_order", 0)
                b["reading_order"] = reading_order + local_order
            reading_order += len(blocks)
        except ImportError:
            # 回退到基础实现
            blocks = sorted(
                blocks,
                key=lambda b: (
                    int(b.get("column_index", 0)),
                    float((b.get("bbox") or {}).get("y0", 0.0)),
                    float((b.get("bbox") or {}).get("x0", 0.0)),
                ),
            )
            for b in blocks:
                b["reading_order"] = reading_order
                reading_order += 1

        # 每处理完一页，更新进度
        if progress_callback:
            progress_callback(page_index + 1, total_pages, {"substage": "merge", "step_done": page_index + 1, "step_total": total_pages, "message": f"页面完成: {page_index + 1}/{total_pages}"})

        pages.append(
            {
                "index": page_index,
                "width": float(rect.width),
                "height": float(rect.height),
                "blocks": blocks,
                "regions": [
                    {
                        "type": r.type,
                        "x0": r.x0,
                        "y0": r.y0,
                        "x1": r.x1,
                        "y1": r.y1,
                        "score": r.score,
                    }
                    for r in regions
                ],
            }
        )

    # v0.8 增强：使用新的布局增强模块
    try:
        from .layout_enhancement import enhance_layout_processing

        enhance_layout_processing(
            pages,
            enable_header_footer_detection=True,
            enable_footnote_enhancement=True,
            enable_reading_order_optimization=True,
        )
    except ImportError:
        logger.warning("布局增强模块未找到，使用基础实现")
        # 回退到基础实现（如果新模块不可用）
        pass

    # 文档结构分析（章节/小节层级）
    try:
        struct_info = analyze_document_structure(pages)
        if struct_info.get("sections"):
            structured = {
                "document": {
                    "id": document_id,
                    "project_id": project_id,
                    "title": _extract_original_filename(pdf_path),
                    "num_pages": len(pages),
                    "lang_in": lang_in,
                    "lang_out": lang_out,
                    "status": "parsed",
                    "created_at": now,
                    "updated_at": now,
                },
                "pages": pages,
                "sections": struct_info["sections"],
            }
        else:
            structured = {
                "document": {
                    "id": document_id,
                    "project_id": project_id,
                    "title": _extract_original_filename(pdf_path),
                    "num_pages": len(pages),
                    "lang_in": lang_in,
                    "lang_out": lang_out,
                    "status": "parsed",
                    "created_at": now,
                    "updated_at": now,
                },
                "pages": pages,
            }
    except Exception:
        logger.warning("文档结构分析失败，使用基础结构", exc_info=True)
        structured = {
            "document": {
                "id": document_id,
                "project_id": project_id,
                "title": _extract_original_filename(pdf_path),
                "num_pages": len(pages),
                "lang_in": lang_in,
                "lang_out": lang_out,
                "status": "parsed",
                "created_at": now,
                "updated_at": now,
            },
            "pages": pages,
        }

    doc.close()

    # 保存到缓存
    if use_cache:
        try:
            from .pdf_cache import get_pdf_parse_cache

            cache = get_pdf_parse_cache()
            cache.set(
                pdf_path,
                structured,
                use_hybrid_parser=use_hybrid_parser,
                use_feature_based_layout=use_feature_based_layout,
                vfont=vfont,
                vchar=vchar,
            )
            logger.info(f"PDF解析结果已缓存: {pdf_path.name}")
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")

    return structured


