from __future__ import annotations

"""
轻量级 OCR 封装

优先使用 pytesseract，如未安装则优雅降级为不可用（仅记录日志，不中断主流程）。

本模块只负责“给定页面 -> 返回若干文本块（含 bbox 与文本）”，
具体如何与现有 blocks 融合由 pdf_parse 决定。
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any

try:
    import pytesseract  # type: ignore
    from PIL import Image
    OCR_AVAILABLE = True
except Exception:  # pragma: no cover - 运行环境未必安装 OCR 依赖
    pytesseract = None  # type: ignore
    Image = None  # type: ignore
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class OCRBlock:
    """OCR 识别到的一个文本块（行级别）"""

    x0: float
    y0: float
    x1: float
    y1: float
    text: str


def run_ocr_on_page(page, *, dpi: int = 300) -> List[OCRBlock]:
    """
    对单页执行 OCR，返回若干文本块。

    Args:
        page: PyMuPDF page 对象
        dpi: 渲染分辨率（默认 300）

    Returns:
        OCRBlock 列表；如果 OCR 不可用或失败，返回空列表。
    """
    if not OCR_AVAILABLE:
        logger.debug("OCR 依赖未安装，跳过 OCR 识别")
        return []

    try:
        # 将页面渲染为位图
        zoom = dpi / 72.0
        mat = page.get_mat().pre_scale(zoom, zoom) if hasattr(page, "get_mat") else None
        pix = page.get_pixmap(matrix=mat) if mat is not None else page.get_pixmap(dpi=dpi)

        mode = "RGB" if pix.alpha == 0 else "RGBA"
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)

        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        blocks: List[OCRBlock] = []
        n_boxes = len(data.get("text", []))
        if n_boxes == 0:
            return []

        # 将 tesseract 坐标（基于渲染像素）映射回 PDF 坐标
        page_width = float(page.rect.width)
        page_height = float(page.rect.height)
        scale_x = page_width / float(pix.width or 1)
        scale_y = page_height / float(pix.height or 1)

        for i in range(n_boxes):
            txt = (data["text"][i] or "").strip()
            if not txt:
                continue
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            x0 = x * scale_x
            y0 = y * scale_y
            x1 = (x + w) * scale_x
            y1 = (y + h) * scale_y
            blocks.append(OCRBlock(x0=x0, y0=y0, x1=x1, y1=y1, text=txt))

        if blocks:
            logger.info("OCR 识别完成：page=%s blocks=%s", page.number + 1, len(blocks))

        return blocks
    except Exception as exc:  # pragma: no cover - OCR 失败不应中断主流程
        logger.warning("OCR 识别失败，将继续使用原有解析: %s", exc, exc_info=True)
        return []


