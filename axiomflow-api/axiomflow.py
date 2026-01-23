#!/usr/bin/env python3
"""
AxiomFlow CLI - 命令行 PDF 翻译工具

支持单个文件、批量文件和目录翻译，输出多种格式（PDF mono/dual, Markdown, HTML）。
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# 禁用第三方库的日志
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("openai").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="AxiomFlow CLI - PDF 翻译工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
                示例:
                # 翻译单个文件
                axiomflow document.pdf

                # 翻译多个文件
                axiomflow file1.pdf file2.pdf -o ./output

                # 批量翻译目录
                axiomflow --dir ./pdfs -o ./output

                # 指定语言和翻译服务
                axiomflow document.pdf --lang-in en --lang-out zh --provider ollama

                # 导出为 Markdown
                axiomflow document.pdf --format markdown

                # 导出为 PDF（单语/双语）
                axiomflow document.pdf --format pdf-mono
                axiomflow document.pdf --format pdf-dual
                        """,
    )

    # 位置参数：PDF 文件或目录
    parser.add_argument(
        "files",
        nargs="*",
        help="PDF 文件路径（支持多个文件）",
    )

    # 版本信息
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="AxiomFlow CLI v0.1.0",
    )

    # 调试模式
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="启用调试日志",
    )

    # 解析参数组
    parse_group = parser.add_argument_group("解析选项", "PDF 解析相关选项")
    parse_group.add_argument(
        "--pages",
        "-p",
        type=str,
        help="指定要翻译的页码，格式：1,3,5-10（从 1 开始）",
    )
    parse_group.add_argument(
        "--vfont",
        "-f",
        type=str,
        default="",
        help="公式字体匹配正则表达式（用于识别公式字体）",
    )
    parse_group.add_argument(
        "--vchar",
        "-c",
        type=str,
        default="",
        help="公式字符匹配正则表达式（用于识别公式字符）",
    )
    parse_group.add_argument(
        "--ocr",
        action="store_true",
        default=True,
        help="启用OCR识别扫描版PDF（默认: 启用）",
    )
    parse_group.add_argument(
        "--no-ocr",
        dest="ocr",
        action="store_false",
        help="禁用OCR识别",
    )
    parse_group.add_argument(
        "--ocr-engine",
        type=str,
        choices=["auto", "tesseract", "easyocr", "paddleocr"],
        default="auto",
        help="OCR引擎选择（默认: auto，自动选择最佳引擎）",
    )
    parse_group.add_argument(
        "--lang-in",
        "-li",
        type=str,
        default="en",
        help="源语言代码（默认: en）",
    )
    parse_group.add_argument(
        "--lang-out",
        "-lo",
        type=str,
        default="zh",
        help="目标语言代码（默认: zh）",
    )

    # 翻译参数组
    translate_group = parser.add_argument_group("翻译选项", "翻译服务相关选项")
    translate_group.add_argument(
        "--provider",
        "-s",
        type=str,
        default="ollama",
        help="翻译服务提供商（默认: ollama）。支持的服务: ollama",
    )
    translate_group.add_argument(
        "--list-providers",
        action="store_true",
        help="列出所有可用的翻译服务提供商",
    )
    translate_group.add_argument(
        "--glossary",
        "-g",
        type=str,
        help="术语表文件路径（JSON 格式：{\"term\": \"translation\"}）",
    )

    # 输出参数组
    output_group = parser.add_argument_group("输出选项", "输出格式和路径相关选项")
    output_group.add_argument(
        "--output",
        "-o",
        type=str,
        default=".",
        help="输出目录（默认: 当前目录）",
    )
    output_group.add_argument(
        "--format",
        "-fmt",
        type=str,
        choices=["pdf-mono", "pdf-dual", "markdown", "html", "json", "all"],
        default="pdf-dual",
        help="输出格式（默认: pdf-dual）。支持: pdf-mono（单语PDF）, pdf-dual（双语PDF）, markdown, html, json（结构化JSON）, all（所有格式）",
    )
    output_group.add_argument(
        "--subset-fonts",
        action="store_true",
        default=True,
        help="启用字体子集化（默认: 启用）",
    )
    output_group.add_argument(
        "--no-subset-fonts",
        dest="subset_fonts",
        action="store_false",
        help="禁用字体子集化",
    )
    output_group.add_argument(
        "--pdfa",
        action="store_true",
        help="转换为 PDF/A 格式（提高兼容性）",
    )

    # 批量处理参数组
    batch_group = parser.add_argument_group("批量处理", "批量翻译相关选项")
    batch_group.add_argument(
        "--dir",
        "-d",
        action="store_true",
        help="批量处理目录中的所有 PDF 文件",
    )
    batch_group.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="递归搜索子目录（与 --dir 一起使用）",
    )
    batch_group.add_argument(
        "--threads",
        "-t",
        type=int,
        default=1,
        help="并发翻译线程数（默认: 1，串行处理）",
    )

    # 其他选项
    other_group = parser.add_argument_group("其他选项")
    other_group.add_argument(
        "--ignore-cache",
        action="store_true",
        help="忽略翻译缓存，强制重新翻译",
    )
    other_group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="静默模式，减少输出",
    )

    return parser


def parse_pages(pages_str: str) -> list[int]:
    """解析页码字符串，返回从 0 开始的页码列表"""
    pages = []
    for p in pages_str.split(","):
        p = p.strip()
        if "-" in p:
            start, end = p.split("-", 1)
            start = int(start.strip()) - 1  # 转换为从 0 开始
            end = int(end.strip())  # 结束页码（不包含）
            pages.extend(range(start, end))
        else:
            pages.append(int(p.strip()) - 1)  # 转换为从 0 开始
    return sorted(set(pages))  # 去重并排序


def find_pdf_files(path: Path, recursive: bool = False) -> list[Path]:
    """查找目录中的所有 PDF 文件"""
    pdf_files = []
    if path.is_file() and path.suffix.lower() == ".pdf":
        return [path]
    if path.is_dir():
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = list(path.glob(pattern))
    return sorted(pdf_files)


async def translate_single_file(
    pdf_path: Path,
    output_dir: Path,
    lang_in: str,
    lang_out: str,
    provider: str,
    output_format: str,
    pages: Optional[list[int]] = None,
    glossary: Optional[dict[str, str]] = None,
    subset_fonts: bool = True,
    pdfa: bool = False,
    quiet: bool = False,
    enable_ocr: bool = True,
    ocr_engine: str = "auto",
) -> dict[str, Path]:
    """
    翻译单个 PDF 文件

    Returns:
        输出文件路径字典：{"mono": Path, "dual": Path, "markdown": Path, "html": Path}
    """
    try:
        from app.repo import get_repo
        from app.core.config import settings
        from app.services.pdf_parse import parse_pdf_to_structured_json
        from app.services.orchestrator import TranslateOrchestrator, TranslateStrategy
        from app.services.providers.base import TranslateMeta
        from app.services.pdf_export import build_translated_pdf
    except ImportError:
        # 如果直接运行脚本，添加路径
        import sys
        from pathlib import Path
        _current_dir = Path(__file__).resolve().parent
        sys.path.insert(0, str(_current_dir))
        from app.repo import get_repo
        from app.core.config import settings
        from app.services.pdf_parse import parse_pdf_to_structured_json
        from app.services.orchestrator import TranslateOrchestrator, TranslateStrategy
        from app.services.providers.base import TranslateMeta
        from app.services.pdf_export import build_translated_pdf

    # 初始化 repo（使用内存存储，CLI 模式不需要持久化）
    repo = get_repo()

    # 创建临时项目
    project_id = repo.create_project(f"CLI_{pdf_path.stem}")

    # 加载术语表
    if glossary:
        for term, translation in glossary.items():
            repo.upsert_glossary_term(project_id, term, translation)

    # 读取 PDF
    pdf_content = pdf_path.read_bytes()
    document_id, pdf_storage_path = repo.save_upload(pdf_path.name, pdf_content)

    # 解析 PDF
    if not quiet:
        logger.info(f"正在解析 PDF: {pdf_path.name}")
    structured = parse_pdf_to_structured_json(
        pdf_storage_path,
        document_id=document_id,
        project_id=project_id,
        lang_in=lang_in,
        lang_out=lang_out,
        enable_ocr=args.ocr if hasattr(args, 'ocr') else True,
        ocr_engine=args.ocr_engine if hasattr(args, 'ocr_engine') else "auto",
        vfont=args.vfont if hasattr(args, 'vfont') else "",
        vchar=args.vchar if hasattr(args, 'vchar') else "",
        use_cache=True,  # 默认启用缓存
    )
    structured.setdefault("document", {})["source_pdf_path"] = pdf_storage_path.as_posix()

    # 过滤页码
    if pages is not None:
        total_pages = len(structured.get("pages", []))
        filtered_pages = [p for i, p in enumerate(structured.get("pages", [])) if i in pages]
        structured["pages"] = filtered_pages
        if not quiet:
            logger.info(f"已过滤到 {len(filtered_pages)}/{total_pages} 页")

    # 保存结构化数据
    repo.save_document_json(document_id, structured)

    # 翻译（使用批量翻译，支持上下文感知、术语一致性等）
    if not quiet:
        logger.info(f"正在翻译（使用 {provider} 服务）...")
    orch = TranslateOrchestrator()
    
    # 构建翻译策略（启用所有高级功能）
    strategy = TranslateStrategy(
        provider=provider,
        use_context=True,  # 启用上下文感知翻译
        context_window_size=2,
        use_term_consistency=True,  # 启用术语一致性检查
        use_smart_batching=True,  # 启用智能批处理
    )
    
    glossary_dict = glossary or {}
    meta_template = TranslateMeta(
        lang_in=lang_in,
        lang_out=lang_out,
        document_id=document_id,
        block_type=None,
        glossary=glossary_dict or None,
    )
    
    # 收集所有需要翻译的块
    all_blocks: list[dict[str, Any]] = []
    for page in structured.get("pages", []):
        for block in page.get("blocks", []):
            # 确保块有 page_index
            if "page_index" not in block:
                block["page_index"] = structured.get("pages", []).index(page)
            all_blocks.append(block)
    
    # 使用批量翻译（支持上下文感知、术语一致性、智能批处理）
    def progress_callback(done_count: int, total_count: int) -> None:
        if not quiet and total_count > 0:
            progress = done_count / total_count * 100
            print(f"\r进度: {progress:.1f}% ({done_count}/{total_count})", end="", flush=True)
    
    await orch.translate_blocks_batch(
        all_blocks,
        meta_template,
        strategy,
        progress_callback=progress_callback,
    )
    
    if not quiet:
        print()  # 换行

    # 保存翻译结果
    repo.save_document_json(document_id, structured)

    # 导出
    output_files = {}
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = pdf_path.stem

    if output_format in ("pdf-mono", "pdf-dual", "all"):
        if output_format in ("pdf-mono", "all"):
            if not quiet:
                logger.info("正在导出单语 PDF...")
            mono_path = output_dir / f"{base_name}-mono.pdf"
            pdf_bytes = build_translated_pdf(
                structured,
                bilingual=False,
                subset_fonts=subset_fonts,
                convert_to_pdfa=pdfa,
            )
            mono_path.write_bytes(pdf_bytes)
            output_files["mono"] = mono_path
            if not quiet:
                logger.info(f"✓ 单语 PDF: {mono_path}")

        if output_format in ("pdf-dual", "all"):
            if not quiet:
                logger.info("正在导出双语 PDF...")
            dual_path = output_dir / f"{base_name}-dual.pdf"
            pdf_bytes = build_translated_pdf(
                structured,
                bilingual=True,
                subset_fonts=subset_fonts,
                convert_to_pdfa=pdfa,
            )
            dual_path.write_bytes(pdf_bytes)
            output_files["dual"] = dual_path
            if not quiet:
                logger.info(f"✓ 双语 PDF: {dual_path}")

    if output_format in ("markdown", "all"):
        if not quiet:
            logger.info("正在导出 Markdown...")
        md_path = output_dir / f"{base_name}.md"
        md_content = _export_markdown(structured, bilingual=False)
        md_path.write_text(md_content, encoding="utf-8")
        output_files["markdown"] = md_path
        if not quiet:
            logger.info(f"✓ Markdown: {md_path}")

    if output_format in ("html", "all"):
        if not quiet:
            logger.info("正在导出 HTML...")
        html_path = output_dir / f"{base_name}.html"
        html_content = _export_html(structured, bilingual=False)
        html_path.write_text(html_content, encoding="utf-8")
        output_files["html"] = html_path
        if not quiet:
            logger.info(f"✓ HTML: {html_path}")

    if output_format in ("json", "all"):
        if not quiet:
            logger.info("正在导出 JSON...")
        import json
        json_path = output_dir / f"{base_name}.json"
        json_content = json.dumps(structured, ensure_ascii=False, indent=2)
        json_path.write_text(json_content, encoding="utf-8")
        output_files["json"] = json_path
        if not quiet:
            logger.info(f"✓ JSON: {json_path}")

    return output_files


def load_glossary(glossary_path: Path) -> dict[str, str]:
    """加载术语表 JSON 文件"""
    import json

    if not glossary_path.exists():
        raise FileNotFoundError(f"术语表文件不存在: {glossary_path}")
    with glossary_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _export_markdown(structured: dict, bilingual: bool = False) -> str:
    """导出为 Markdown 格式"""
    pages = structured.get("pages", [])
    blocks = []
    for p in pages:
        blocks.extend(p.get("blocks", []))
    blocks.sort(key=lambda b: b.get("reading_order", 0))

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

    return "\n".join(lines).strip() + "\n"


def _export_html(structured: dict, bilingual: bool = False) -> str:
    """导出为 HTML 格式"""
    pages = structured.get("pages", [])
    blocks = []
    for p in pages:
        blocks.extend(p.get("blocks", []))
    blocks.sort(key=lambda b: b.get("reading_order", 0))

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
    return "\n".join(parts)


async def main_async(args: argparse.Namespace) -> int:
    """异步主函数"""
    # 列出翻译服务提供商
    if args.list_providers:
        print("可用的翻译服务提供商：")
        print("  - ollama: Ollama 本地模型服务（需要安装 ollama 并运行服务）")
        print("\n使用方法：")
        print("  axiomflow document.pdf --provider ollama")
        return 0

    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # 解析页码
    pages = None
    if args.pages:
        pages = parse_pages(args.pages)

    # 设置公式识别配置（vfont 和 vchar）
    try:
        from app.core.config_manager import config_manager
        if args.vfont:
            config_manager.set("parser.vfont", args.vfont)
            if not args.quiet:
                logger.info(f"设置公式字体正则: {args.vfont}")
        if args.vchar:
            config_manager.set("parser.vchar", args.vchar)
            if not args.quiet:
                logger.info(f"设置公式字符正则: {args.vchar}")
    except ImportError:
        # 如果无法导入，忽略（不影响核心功能）
        pass

    # 加载术语表
    glossary = None
    if args.glossary:
        glossary = load_glossary(Path(args.glossary))

    # 准备输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 查找 PDF 文件
    pdf_files: list[Path] = []
    if args.dir:
        if not args.files:
            logger.error("使用 --dir 选项时，必须指定目录路径")
            return 1
        dir_path = Path(args.files[0])
        if not dir_path.exists():
            logger.error(f"目录不存在: {dir_path}")
            return 1
        pdf_files = find_pdf_files(dir_path, recursive=args.recursive)
        if not pdf_files:
            logger.warning(f"目录中未找到 PDF 文件: {dir_path}")
            return 0
    else:
        if not args.files:
            parser = create_parser()
            parser.print_help()
            return 1
        for f in args.files:
            pdf_path = Path(f)
            if not pdf_path.exists():
                logger.error(f"文件不存在: {pdf_path}")
                return 1
            pdf_files.extend(find_pdf_files(pdf_path, recursive=False))

    if not pdf_files:
        logger.error("未找到任何 PDF 文件")
        return 1

    logger.info(f"找到 {len(pdf_files)} 个 PDF 文件")

    # 翻译文件
    success_count = 0
    fail_count = 0

    if args.threads > 1:
        # 并发翻译
        import concurrent.futures

        async def translate_with_semaphore(pdf_path: Path, semaphore: asyncio.Semaphore):
            async with semaphore:
                try:
                    await translate_single_file(
                        pdf_path,
                        output_dir,
                        args.lang_in,
                        args.lang_out,
                        args.provider,
                        args.format,
                        pages,
                        glossary,
                        args.subset_fonts,
                        args.pdfa,
                        args.quiet,
                        args.ocr if hasattr(args, 'ocr') else True,
                        args.ocr_engine if hasattr(args, 'ocr_engine') else "auto",
                    )
                    return True
                except Exception as e:
                    logger.error(f"翻译失败 {pdf_path}: {e}", exc_info=args.debug)
                    return False

        semaphore = asyncio.Semaphore(args.threads)
        tasks = [translate_with_semaphore(pdf_path, semaphore) for pdf_path in pdf_files]
        results = await asyncio.gather(*tasks)
        success_count = sum(results)
        fail_count = len(results) - success_count
    else:
        # 串行翻译
        for pdf_path in pdf_files:
            try:
                logger.info(f"\n处理文件: {pdf_path.name}")
                await translate_single_file(
                    pdf_path,
                    output_dir,
                    args.lang_in,
                    args.lang_out,
                    args.provider,
                    args.format,
                    pages,
                    glossary,
                    args.subset_fonts,
                    args.pdfa,
                    args.quiet,
                    args.ocr if hasattr(args, 'ocr') else True,
                    args.ocr_engine if hasattr(args, 'ocr_engine') else "auto",
                )
                success_count += 1
            except Exception as e:
                logger.error(f"翻译失败 {pdf_path}: {e}", exc_info=args.debug)
                fail_count += 1

    # 输出总结
    logger.info(f"\n完成！成功: {success_count}, 失败: {fail_count}")
    return 0 if fail_count == 0 else 1


def main(args: Optional[list[str]] = None) -> int:
    """主入口函数"""
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    return asyncio.run(main_async(parsed_args))


if __name__ == "__main__":
    sys.exit(main())

