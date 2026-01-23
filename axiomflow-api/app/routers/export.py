from fastapi import APIRouter

from ..repo import repo
from ..services.pdf_export import export_pdf, export_docx
from ..services.html_export import build_high_fidelity_html

router = APIRouter(prefix="/export", tags=["export"])


@router.post("")
async def export_document(payload: dict) -> dict:
    """
    v0.7+：导出 Markdown/HTML/PDF（增强版）
    输入：
    - document_id: 文档 ID
    - format: "markdown" | "html" | "html-hifi" | "pdf" | "pdf-mono" | "pdf-dual" | "docx"
    - bilingual: bool (仅用于 markdown/html)
    - subset_fonts: bool (PDF 字体子集化，默认 true)
    - convert_to_pdfa: bool (PDF/A 转换，默认 false)
    """
    document_id = payload.get("document_id")
    fmt = (payload.get("format") or "markdown").lower()
    bilingual = bool(payload.get("bilingual", False))
    subset_fonts = bool(payload.get("subset_fonts", True))  # 默认启用字体子集化
    convert_to_pdfa = bool(payload.get("convert_to_pdfa", False))  # 默认不转换 PDF/A
    pdfa_part = payload.get("pdfa_part")  # 可选: 1/2/3
    pdfa_conformance = (payload.get("pdfa_conformance") or "B").upper()  # "A"|"B"|"U"

    data = repo.load_document_json(document_id)
    pages = data.get("pages", [])
    blocks = []
    for p in pages:
        blocks.extend(p.get("blocks", []))
    blocks.sort(key=lambda b: b.get("reading_order", 0))

    if fmt == "markdown":
        fig_no = 0
        tbl_no = 0
        lines: list[str] = []
        for b in blocks:
            t = (b.get("type") or "paragraph").lower()
            src = (b.get("text") or "").strip()
            dst = (b.get("translation") or "").strip()
            if b.get("is_header_footer"):
                continue
            if b.get("is_footnote"):
                continue
            if t == "heading":
                lines.append(f"## {dst or src}")
                continue
            if t == "caption":
                if bilingual and dst:
                    lines.append(f"> {src}\n>\n> {dst}\n")
                else:
                    lines.append(f"> {dst or src}\n")
                continue
            if t in ("figure", "table"):
                # v0.6+: 给出更像原稿的占位（编号）
                if t == "figure":
                    fig_no += 1
                    label = f"Figure {fig_no}"
                else:
                    tbl_no += 1
                    label = f"Table {tbl_no}"
                lines.append(f"\n> [{label}]\n")
                continue
            if t == "formula":
                lines.append(f"\n{dst or src}\n")
                continue

            if bilingual and dst:
                lines.append(f"{src}\n\n{dst}\n")
            else:
                lines.append(f"{dst or src}\n")

        content = "\n".join(lines).strip() + "\n"
        return {"format": "markdown", "content": content}

    if fmt == "html":
        fig_no = 0
        tbl_no = 0
        parts: list[str] = ['<meta charset="utf-8" />', "<article>"]
        for b in blocks:
            t = (b.get("type") or "paragraph").lower()
            src = (b.get("text") or "").strip()
            dst = (b.get("translation") or "").strip()
            if b.get("is_header_footer"):
                continue
            if b.get("is_footnote"):
                continue
            val = dst or src
            if t == "heading":
                parts.append(f"<h2>{val}</h2>")
                continue
            if t == "caption":
                if bilingual and dst:
                    parts.append(f"<blockquote><p>{src}</p><p>{dst}</p></blockquote>")
                else:
                    parts.append(f"<blockquote><p>{val}</p></blockquote>")
                continue
            if t in ("figure", "table"):
                if t == "figure":
                    fig_no += 1
                    label = f"Figure {fig_no}"
                else:
                    tbl_no += 1
                    label = f"Table {tbl_no}"
                parts.append(f"<blockquote><p>[{label}]</p></blockquote>")
                continue
            if t == "formula":
                parts.append(f"<pre>{val}</pre>")
                continue
            if bilingual and dst:
                parts.append(f"<p>{src}</p><p>{dst}</p>")
            else:
                parts.append(f"<p>{val}</p>")
        parts.append("</article>")
        return {"format": "html", "content": "\n".join(parts)}

    if fmt == "html-hifi":
        content = build_high_fidelity_html(data, bilingual=bilingual)
        return {"format": "html", "content": content}

    if fmt in ("pdf", "pdf-mono"):
        filename, pdf_bytes = export_pdf(
            data,
            kind="mono",
            subset_fonts=subset_fonts,
            convert_to_pdfa=convert_to_pdfa,
            pdfa_part=pdfa_part,
            pdfa_conformance=pdfa_conformance,
        )
        repo.save_export_file(filename, pdf_bytes)
        return {
            "format": "pdf",
            "download_url": f"/v1/downloads/{filename}",
            "filename": filename,
        }

    if fmt == "pdf-dual":
        filename, pdf_bytes = export_pdf(
            data,
            kind="dual",
            subset_fonts=subset_fonts,
            convert_to_pdfa=convert_to_pdfa,
            pdfa_part=pdfa_part,
            pdfa_conformance=pdfa_conformance,
        )
        repo.save_export_file(filename, pdf_bytes)
        return {
            "format": "pdf",
            "download_url": f"/v1/downloads/{filename}",
            "filename": filename,
        }

    if fmt == "docx":
        filename, docx_bytes = export_docx(data, bilingual=bilingual)
        repo.save_export_file(filename, docx_bytes)
        return {
            "format": "docx",
            "download_url": f"/v1/downloads/{filename}",
            "filename": filename,
        }

    return {"error": "unsupported_format"}


