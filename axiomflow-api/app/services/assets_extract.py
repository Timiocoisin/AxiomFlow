from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


@dataclass(frozen=True)
class AssetInfo:
    kind: str  # "figure" | "table"
    page_index: int
    x0: float
    y0: float
    x1: float
    y1: float
    rel_path: str


def extract_assets_from_structured(structured: dict, *, out_dir: Path) -> list[AssetInfo]:
    """
    从结构化 JSON 的 pages[].regions 中裁剪 figure/table 为 PNG。
    依赖 document.source_pdf_path。
    """
    doc_meta = structured.get("document", {})
    src_path = doc_meta.get("source_pdf_path")
    if not src_path:
        return []

    pdf = fitz.open(src_path)
    assets: list[AssetInfo] = []

    for p in structured.get("pages", []):
        page_index = int(p.get("index") or 0)
        if page_index < 0 or page_index >= pdf.page_count:
            continue
        page = pdf.load_page(page_index)

        regions = p.get("regions", []) or []
        fig_i = 0
        tbl_i = 0
        for r in regions:
            kind = (r.get("type") or "").lower()
            if kind not in ("figure", "table"):
                continue
            x0, y0, x1, y1 = float(r["x0"]), float(r["y0"]), float(r["x1"]), float(r["y1"])
            clip = fitz.Rect(x0, y0, x1, y1)
            pix = page.get_pixmap(clip=clip, dpi=200, alpha=False)

            if kind == "figure":
                fig_i += 1
                name = f"figure_p{page_index+1}_{fig_i}.png"
            else:
                tbl_i += 1
                name = f"table_p{page_index+1}_{tbl_i}.png"

            out_path = out_dir / name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(pix.tobytes("png"))
            assets.append(
                AssetInfo(
                    kind=kind,
                    page_index=page_index,
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    rel_path=name,
                )
            )

    pdf.close()
    return assets


