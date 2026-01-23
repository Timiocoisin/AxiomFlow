from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal
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


def _parse_scanned_pdf_with_ocr(
    pdf_path: Path,
    *,
    document_id: str,
    project_id: str,
    lang_in: str,
    lang_out: str,
    ocr_engine: str = "auto",
    use_feature_based_layout: bool = True,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> dict:
    """
    使用OCR解析扫描版PDF
    
    Args:
        pdf_path: PDF文件路径
        document_id: 文档ID
        project_id: 项目ID
        lang_in: 源语言
        lang_out: 目标语言
        ocr_engine: OCR引擎类型
        use_feature_based_layout: 是否使用基于特征的布局检测
    
    Returns:
        结构化文档JSON
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from .ocr_service import get_ocr_service
        
        # 确定OCR语言代码
        ocr_lang_map = {
            "en": "eng",
            "zh": "chi_sim",
            "zh-CN": "chi_sim",
            "zh-TW": "chi_tra",
            "ja": "jpn",
            "ko": "kor",
        }
        ocr_lang = ocr_lang_map.get(lang_in, "eng")
        if lang_in == "zh" and lang_out == "en":
            # 中英混合
            ocr_lang = "eng+chi_sim"
        elif lang_in == "en" and lang_out == "zh":
            # 英中混合
            ocr_lang = "eng+chi_sim"
        
        # 初始化OCR服务
        ocr_service = get_ocr_service(engine=ocr_engine, lang=ocr_lang)
        
        now = datetime.utcnow().isoformat()
        doc = fitz.open(pdf_path.as_posix())
        total_pages = doc.page_count
        pages = []
        reading_order = 0
        
        logger.info(f"开始OCR识别，共 {total_pages} 页...")
        
        # 如果有进度回调，先通知总页数
        if progress_callback:
            progress_callback(0, total_pages)
        
        for page_index in range(total_pages):
            if page_index % 10 == 0:
                logger.info(f"正在处理第 {page_index + 1}/{doc.page_count} 页...")
            
            page = doc.load_page(page_index)
            rect = page.rect
            
            # 执行OCR识别
            ocr_result = ocr_service.recognize_page(pdf_path, page_index, dpi=300)
            
            if not ocr_result.text.strip():
                logger.warning(f"第 {page_index + 1} 页OCR未识别到文本")
                # 创建一个空页面
                # 每处理完一页，更新进度
                if progress_callback:
                    progress_callback(page_index + 1, total_pages)
                
                pages.append({
                    "index": page_index,
                    "width": float(rect.width),
                    "height": float(rect.height),
                    "blocks": [],
                    "regions": [],
                })
                continue
            
            # 将OCR结果转换为blocks
            blocks = []
            
            if ocr_result.words:
                # 如果有单词级别信息，创建更精确的blocks
                for word_idx, word_info in enumerate(ocr_result.words):
                    word_text = word_info.get('text', '').strip()
                    if not word_text:
                        continue
                    
                    word_bbox = word_info.get('bbox', (0, 0, 0, 0))
                    x0, y0, x1, y1 = word_bbox
                    
                    # 缩放坐标（OCR可能使用了不同的DPI）
                    # 这里假设OCR返回的是像素坐标，需要转换为PDF坐标
                    # 实际转换可能需要根据OCR引擎调整
                    
                    block_id = new_id("blk")
                    block_type = _guess_block_type(word_text)
                    column_index = _guess_column_index(x0, rect.width)
                    hf = _is_header_or_footer(y0, y1, rect.height)
                    
                    block_dict = {
                        "id": block_id,
                        "document_id": document_id,
                        "type": block_type,
                        "bbox": {
                            "page": page_index,
                            "x0": float(x0),
                            "y0": float(y0),
                            "x1": float(x1),
                            "y1": float(y1),
                        },
                        "reading_order": reading_order,
                        "column_index": column_index,
                        "page_index": page_index,
                        "is_header_footer": hf,
                        "text": word_text,
                        "translation": None,
                        "edited": False,
                        "edited_at": None,
                        "ocr_confidence": word_info.get('confidence', 0.0),
                    }
                    blocks.append(block_dict)
                    reading_order += 1
            else:
                # 如果没有单词级别信息，将整页文本作为一个block
                block_id = new_id("blk")
                block_type = _guess_block_type(ocr_result.text)
                
                # 估算边界框（整页）
                margin = 50  # 页边距
                x0 = margin
                y0 = margin
                x1 = float(rect.width) - margin
                y1 = float(rect.height) - margin
                
                column_index = _guess_column_index(x0, rect.width)
                
                block_dict = {
                    "id": block_id,
                    "document_id": document_id,
                    "type": block_type,
                    "bbox": {
                        "page": page_index,
                        "x0": float(x0),
                        "y0": float(y0),
                        "x1": float(x1),
                        "y1": float(y1),
                    },
                    "reading_order": reading_order,
                    "column_index": column_index,
                    "page_index": page_index,
                    "is_header_footer": None,
                    "text": ocr_result.text,
                    "translation": None,
                    "edited": False,
                    "edited_at": None,
                    "ocr_confidence": ocr_result.confidence,
                }
                blocks.append(block_dict)
                reading_order += 1
            
            # 合并段落块
            blocks = _merge_paragraph_blocks(blocks, page_height=float(rect.height))
            
            # 布局检测
            if use_feature_based_layout:
                try:
                    regions = detect_regions_feature_based(
                        blocks,
                        page_width=float(rect.width),
                        page_height=float(rect.height),
                        use_ml=True,
                        min_confidence=0.4,
                    )
                except Exception as e:
                    logger.warning(f"特征检测失败，回退到启发式方法: {e}")
                    regions = detect_regions_heuristic(blocks)
            else:
                regions = detect_regions_heuristic(blocks)
            
            apply_regions_to_blocks(blocks, regions)
            
            # 重新排序
            blocks = sorted(
                blocks,
                key=lambda b: (
                    int(b.get("column_index", 0)),
                    float((b.get("bbox") or {}).get("y0", 0.0)),
                    float((b.get("bbox") or {}).get("x0", 0.0)),
                ),
            )
            for idx, b in enumerate(blocks):
                b["reading_order"] = reading_order
                reading_order += 1
            
            # 每处理完一页，更新进度
            if progress_callback:
                progress_callback(page_index + 1, total_pages)
            
            pages.append({
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
            })
        
        doc.close()
        logger.info("OCR识别完成")
        
        # 构建结构化文档（与常规解析格式一致）
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
                "source_pdf_path": str(pdf_path),
                "parsed_with_ocr": True,  # 标记使用了OCR
            },
            "pages": pages,
        }
        # 对 OCR 结果同样执行高级布局增强（跨页页眉/页脚、脚注、阅读顺序）
        try:
            from .layout_enhancement import enhance_layout_processing

            enhance_layout_processing(
                structured["pages"],
                enable_header_footer_detection=True,
                enable_footnote_enhancement=True,
                enable_reading_order_optimization=True,
            )
        except Exception:
            # 布局增强失败时不影响 OCR 主流程
            logger.warning("布局增强模块在 OCR 流程中执行失败，继续返回基础结果", exc_info=True)

        # 文档结构分析（章节/小节层级）
        try:
            struct_info = analyze_document_structure(structured["pages"])
            if struct_info.get("sections"):
                structured["sections"] = struct_info["sections"]
        except Exception:
            logger.warning("文档结构分析在 OCR 流程中失败，继续返回基础结果", exc_info=True)

        # OCR 路径暂不走 pdf_parse_cache（通常用于一次性解析），直接返回
        return structured
    except Exception as e:
        logger.error(f"OCR解析失败: {e}", exc_info=True)
        # 如果OCR失败，回退到常规解析
        logger.warning("回退到常规PDF解析...")
        return parse_pdf_to_structured_json(
            pdf_path,
            document_id=document_id,
            project_id=project_id,
            lang_in=lang_in,
            lang_out=lang_out,
            use_hybrid_parser=False,
            enable_ocr=False,
        )


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
    enable_ocr: bool = True,
    ocr_engine: str = "auto",
    vfont: str = "",
    vchar: str = "",
    use_cache: bool = True,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> dict:
    """
    解析 PDF 为结构化 JSON：
    - 使用 PyMuPDF 提取每页 text blocks（含 bbox）；
    - 粗粒度推断 Block.type（heading/paragraph/caption）；
    - 估计列索引 column_index，后续可用于阅读顺序与布局增强。
    - 支持OCR识别扫描版PDF
    - 支持解析结果缓存（基于文件哈希）
    
    Args:
        pdf_path: PDF文件路径
        document_id: 文档ID
        project_id: 项目ID
        lang_in: 源语言
        lang_out: 目标语言
        use_hybrid_parser: 是否使用混合解析器（PyMuPDF + PDFMiner）
        enable_ocr: 是否启用OCR（自动检测扫描PDF）
        ocr_engine: OCR引擎（"auto", "tesseract", "easyocr", "paddleocr")
        vfont: 公式字体匹配正则表达式
        vchar: 公式字符匹配正则表达式
        use_cache: 是否使用缓存
    
    Returns:
        结构化文档JSON
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 尝试从缓存获取
    if use_cache:
        try:
            from .pdf_cache import get_pdf_parse_cache
            
            cache = get_pdf_parse_cache()
            cached_result = cache.get(
                pdf_path,
                use_hybrid_parser=use_hybrid_parser,
                use_feature_based_layout=use_feature_based_layout,
                enable_ocr=enable_ocr,
                ocr_engine=ocr_engine,
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
    
    # 检测是否为扫描PDF，如果是则使用OCR
    if enable_ocr:
        try:
            from .ocr_service import is_scanned_pdf, get_ocr_service
            
            is_scanned = is_scanned_pdf(pdf_path, page_index=0)
            if is_scanned:
                logger.info(f"检测到扫描PDF，启用OCR识别: {pdf_path.name}")
                # 使用OCR解析
                return _parse_scanned_pdf_with_ocr(
                    pdf_path,
                    document_id=document_id,
                    project_id=project_id,
                    lang_in=lang_in,
                    lang_out=lang_out,
                    ocr_engine=ocr_engine,
                    use_feature_based_layout=use_feature_based_layout,
                    progress_callback=progress_callback,
                )
        except Exception as e:
            logger.warning(f"OCR检测或初始化失败，使用常规解析: {e}")
            # 继续使用常规解析
    
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
                enable_ocr=False,  # 避免再次检测
            )
    now = datetime.utcnow().isoformat()
    doc = fitz.open(pdf_path.as_posix())
    total_pages = doc.page_count
    
    # 如果有进度回调，先通知总页数
    if progress_callback:
        progress_callback(0, total_pages)
    
    pages = []
    reading_order = 0

    for page_index in range(total_pages):
        page = doc.load_page(page_index)
        rect = page.rect

        # 提取字体信息（使用 dict 格式获取详细字体信息）
        text_dict = page.get_text("dict")
        font_map = extract_fonts_from_text_dict(text_dict)

        blocks = []
        # (x0, y0, x1, y1, "text", block_no, block_type)
        block_dict_items = page.get_text("blocks")
        text_block_counter = 0  # 只计数有文本的块
        
        for b in block_dict_items:
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

        # v0.7: layout regions (特征工程 + 轻量ML分类器)
        # 优先使用基于特征的检测器（与开源项目不同的方案）
        if use_feature_based_layout:
            try:
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
            progress_callback(page_index + 1, total_pages)

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
                enable_ocr=enable_ocr,
                ocr_engine=ocr_engine,
                vfont=vfont,
                vchar=vchar,
            )
            logger.info(f"PDF解析结果已缓存: {pdf_path.name}")
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")

    return structured


