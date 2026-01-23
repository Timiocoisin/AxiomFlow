from __future__ import annotations

from html import escape


def build_high_fidelity_html(structured: dict, *, bilingual: bool = False) -> str:
    """
    构建高保真 HTML：
    - 保留分页信息（page-index）
    - 保留 block 元数据（id/type/section/reading_order/bbox）
    - 不导出页眉页脚、脚注正文（可通过 data 标记保留）
    """
    document = structured.get("document", {}) or {}
    title = document.get("title") or document.get("id") or "Document"

    pages = structured.get("pages", []) or []

    parts: list[str] = []
    parts.append('<!DOCTYPE html>')
    parts.append('<html lang="en">')
    parts.append('<head>')
    parts.append('<meta charset="utf-8" />')
    parts.append(f"<title>{escape(str(title))}</title>")
    # 简单内联样式，方便直接打开预览
    parts.append(
        """
<style>
body { font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans","Liberation Sans",sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
.doc { max-width: 900px; margin: 0 auto; padding: 24px 16px 64px; background: #ffffff; box-shadow: 0 0 0 1px rgba(15,23,42,.06),0 18px 40px rgba(15,23,42,.18); }
.page { border-bottom: 1px dashed #e5e5e5; padding: 16px 8px 32px; position: relative; }
.page:last-child { border-bottom: none; }
.page-label { position: absolute; right: 0; top: 0; font-size: 11px; color: #999; }
.block { margin: 4px 0 8px; }
.block-heading { margin-top: 16px; margin-bottom: 8px; font-weight: 600; }
.block-caption { font-size: 13px; color: #555; }
.block-figure, .block-table { font-size: 13px; color: #666; }
.block-formula { font-family: "SF Mono","Menlo","Consolas","Liberation Mono",monospace; background: #f9fafb; padding: 6px 8px; border-radius: 4px; }
.src-text { color: #555; }
.dst-text { color: #111; }
.bilingual-pair { margin-bottom: 8px; }
.bilingual-src { font-size: 13px; color: #777; }
.bilingual-dst { margin-top: 2px; }
.meta { font-size: 11px; color: #aaa; }
</style>
        """.strip()
    )
    parts.append("</head>")
    parts.append("<body>")
    parts.append('<div class="doc">')

    for page in pages:
        page_index = int(page.get("index") or 0)
        blocks = list(page.get("blocks", []) or [])
        blocks.sort(key=lambda b: int(b.get("reading_order", 0)))

        parts.append(f'<section class="page" data-page-index="{page_index}">')
        parts.append(f'<div class="page-label">Page {page_index + 1}</div>')

        for blk in blocks:
            blk_type = (blk.get("type") or "paragraph").lower()
            blk_id = blk.get("id") or ""
            section_id = blk.get("section_id") or ""
            section_level = blk.get("section_level")
            reading_order = blk.get("reading_order")

            bbox = blk.get("bbox") or {}
            x0 = bbox.get("x0")
            y0 = bbox.get("y0")
            x1 = bbox.get("x1")
            y1 = bbox.get("y1")

            is_header_footer = bool(blk.get("is_header_footer"))
            is_footnote = bool(blk.get("is_footnote"))

            src = (blk.get("text") or "").strip()
            dst = (blk.get("translation") or "").strip()

            # 页眉/页脚、脚注不直接展示正文，但以 meta 标记保留
            if is_header_footer or is_footnote:
                meta_kinds: list[str] = []
                if is_header_footer:
                    meta_kinds.append("header_footer")
                if is_footnote:
                    meta_kinds.append("footnote")
                meta_kind = ",".join(meta_kinds)
                parts.append(
                    f'<div class="block meta" data-kind="{meta_kind}" '
                    f'data-id="{escape(str(blk_id))}" '
                    f'data-type="{escape(blk_type)}" '
                    f'data-section-id="{escape(str(section_id))}" '
                    f'data-section-level="{escape(str(section_level))}" '
                    f'data-reading-order="{escape(str(reading_order))}" '
                    f'data-bbox-x0="{escape(str(x0))}" '
                    f'data-bbox-y0="{escape(str(y0))}" '
                    f'data-bbox-x1="{escape(str(x1))}" '
                    f'data-bbox-y1="{escape(str(y1))}"'
                    f">"
                    f"{escape(src or dst)[:80]}"
                    f"</div>"
                )
                continue

            classes = ["block", f"block-{blk_type}"]
            attr = (
                f'data-id="{escape(str(blk_id))}" '
                f'data-type="{escape(blk_type)}" '
                f'data-section-id="{escape(str(section_id))}" '
                f'data-section-level="{escape(str(section_level))}" '
                f'data-reading-order="{escape(str(reading_order))}" '
                f'data-bbox-x0="{escape(str(x0))}" '
                f'data-bbox-y0="{escape(str(y0))}" '
                f'data-bbox-x1="{escape(str(x1))}" '
                f'data-bbox-y1="{escape(str(y1))}"'
            )

            parts.append(f'<div class="{" ".join(classes)}" {attr}>')

            # 标题
            if blk_type == "heading":
                level = int(section_level or 1)
                level = max(1, min(level, 3))
                tag = f"h{level+1}" if level < 5 else "h5"
                text = dst or src
                parts.append(f"<{tag}>{escape(text)}</{tag}>")

            # 图表标题
            elif blk_type == "caption":
                if bilingual and dst:
                    parts.append('<div class="bilingual-pair">')
                    parts.append(
                        f'<div class="bilingual-src">{escape(src)}</div>'
                    )
                    parts.append(
                        f'<div class="bilingual-dst">{escape(dst)}</div>'
                    )
                    parts.append("</div>")
                else:
                    parts.append(f'<div class="block-caption">{escape(dst or src)}</div>')

            # 图/表占位
            elif blk_type in ("figure", "table"):
                label = blk_type.capitalize()
                parts.append(
                    f'<div class="block-{blk_type}">[{label}] {escape(dst or src)}</div>'
                )

            # 公式
            elif blk_type == "formula":
                parts.append(
                    f'<div class="block-formula">{escape(dst or src)}</div>'
                )

            # 普通段落等
            else:
                if bilingual and dst:
                    parts.append('<div class="bilingual-pair">')
                    parts.append(
                        f'<div class="bilingual-src src-text">{escape(src)}</div>'
                    )
                    parts.append(
                        f'<div class="bilingual-dst dst-text">{escape(dst)}</div>'
                    )
                    parts.append("</div>")
                else:
                    parts.append(
                        f'<div class="dst-text">{escape(dst or src)}</div>'
                    )

            parts.append("</div>")  # .block

        parts.append("</section>")  # .page

    parts.append("</div>")  # .doc
    parts.append("</body>")
    parts.append("</html>")

    return "\n".join(parts)


