"""
混合PDF解析器

结合PyMuPDF（快速）和PDFMiner（深度），根据文档特征自动选择最优解析方式。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

# 避免循环导入：在函数内部导入
# from .pdf_parse import parse_pdf_to_structured_json as pymupdf_parse
from .pdfminer_parser import (
    extract_chars_from_region,
    group_chars_into_blocks,
    analyze_font_pattern,
    CharInfo,
    PDFMINER_AVAILABLE,
)
from .font_hierarchy import FontHierarchyAnalyzer

logger = logging.getLogger(__name__)


class HybridPDFParser:
    """混合PDF解析器：PyMuPDF + PDFMiner"""
    
    def __init__(self, use_deep_parsing: bool = True):
        """
        Args:
            use_deep_parsing: 是否启用深度解析（PDFMiner字符级）
        """
        self.use_deep_parsing = use_deep_parsing
        self.font_analyzer = FontHierarchyAnalyzer()
    
    def parse(
        self,
        pdf_path: Path,
        *,
        document_id: str,
        project_id: str,
        lang_in: str,
        lang_out: str,
    ) -> dict[str, Any]:
        """
        解析PDF文档（混合模式）
        
        策略：
        1. 先用PyMuPDF快速解析
        2. 检测复杂区域（公式、表格、CJK密集区域）
        3. 对复杂区域使用PDFMiner深度解析
        4. 合并结果
        """
        # 避免循环导入：在函数内部导入
        from .pdf_parse import parse_pdf_to_structured_json as pymupdf_parse
        
        # 1. PyMuPDF快速解析（禁用混合解析以避免递归）
        structured = pymupdf_parse(
            pdf_path,
            document_id=document_id,
            project_id=project_id,
            lang_in=lang_in,
            lang_out=lang_out,
            use_hybrid_parser=False,  # 禁用混合解析，避免递归
        )
        
        # 2. 字体层次结构分析
        doc_analysis = self.font_analyzer.analyze_document(structured["pages"])
        
        # 3. 检测需要深度解析的区域
        if self.use_deep_parsing and PDFMINER_AVAILABLE:
            structured = self._enhance_with_deep_parsing(structured, pdf_path)
        elif self.use_deep_parsing and not PDFMINER_AVAILABLE:
            logger.warning("pdfminer.six 未安装，跳过深度解析")
        
        # 4. 添加文档级别的字体分析结果
        structured["document"]["font_analysis"] = doc_analysis
        
        return structured
    
    def _enhance_with_deep_parsing(
        self,
        structured: dict[str, Any],
        pdf_path: Path,
    ) -> dict[str, Any]:
        """
        使用PDFMiner增强结构化结果
        
        对复杂区域（公式、表格、CJK密集）进行字符级深度解析
        """
        pages = structured["pages"]
        
        for page_dict in pages:
            page_index = page_dict["index"]
            blocks = page_dict["blocks"]
            regions = page_dict.get("regions", [])
            
            # 找到公式区域和表格区域
            formula_regions = [r for r in regions if r.get("type") == "formula"]
            table_regions = [r for r in regions if r.get("type") == "table"]
            
            # 对公式区域进行深度解析
            for region in formula_regions:
                try:
                    chars = extract_chars_from_region(
                        pdf_path,
                        page_index,
                        region["x0"],
                        region["y0"],
                        region["x1"],
                        region["y1"],
                    )
                    
                    if chars:
                        # 分析字体模式
                        font_pattern = analyze_font_pattern(chars)
                        region["font_pattern"] = font_pattern
                        
                        # 增强公式检测置信度
                        if font_pattern.get("most_common_font"):
                            font_name = font_pattern["most_common_font"]
                            # 如果字体名匹配数学字体模式，提高置信度
                            if self.font_analyzer._is_math_font(font_name):
                                region["score"] = min(1.0, region.get("score", 0.5) + 0.2)
                        
                        # 检测角标（字体大小突变）
                        if font_pattern.get("has_size_variation"):
                            region["has_subscript_superscript"] = True
                        
                        logger.debug(
                            f"页面 {page_index} 公式区域深度解析: "
                            f"{len(chars)} 个字符, 字体: {font_pattern.get('most_common_font')}"
                        )
                
                except Exception as e:
                    logger.warning(f"公式区域深度解析失败: {e}", exc_info=True)
            
            # 对表格区域进行深度解析
            for region in table_regions:
                try:
                    chars = extract_chars_from_region(
                        pdf_path,
                        page_index,
                        region["x0"],
                        region["y0"],
                        region["x1"],
                        region["y1"],
                    )
                    
                    if chars:
                        # 将字符分组为块（行）
                        char_blocks = group_chars_into_blocks(chars, page_index)
                        
                        # 提取表格结构信息
                        region["char_blocks"] = [
                            {
                                "text": cb.text,
                                "x0": cb.x0,
                                "y0": cb.y0,
                                "x1": cb.x1,
                                "y1": cb.y1,
                                "char_count": len(cb.chars),
                            }
                            for cb in char_blocks
                        ]
                        
                        logger.debug(
                            f"页面 {page_index} 表格区域深度解析: "
                            f"{len(chars)} 个字符, {len(char_blocks)} 行"
                        )
                
                except Exception as e:
                    logger.warning(f"表格区域深度解析失败: {e}", exc_info=True)
            
            # 对CJK密集区域进行深度解析（检查CID字体）
            cjk_blocks = self._detect_cjk_blocks(blocks)
            
            for block in cjk_blocks:
                try:
                    bbox = block.get("bbox", {})
                    if not bbox:
                        continue
                    
                    chars = extract_chars_from_region(
                        pdf_path,
                        page_index,
                        float(bbox["x0"]),
                        float(bbox["y0"]),
                        float(bbox["x1"]),
                        float(bbox["y1"]),
                    )
                    
                    # 检查是否有CID字体（CJK字符的特征）
                    cid_chars = [c for c in chars if c.cid is not None]
                    if cid_chars:
                        block["has_cid_font"] = True
                        block["cid_char_count"] = len(cid_chars)
                        
                        # 更新字体信息
                        if chars:
                            font_pattern = analyze_font_pattern(chars)
                            if "font" not in block:
                                block["font"] = {}
                            block["font"]["deep_analysis"] = font_pattern
                
                except Exception as e:
                    logger.warning(f"CJK块深度解析失败: {e}", exc_info=True)
            
            # 更新页面的regions
            page_dict["regions"] = [
                {**r, "enhanced": True} if isinstance(r, dict) else r
                for r in regions
            ]
        
        return structured
    
    def _detect_cjk_blocks(self, blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        检测CJK（中日韩）文本密集的块
        
        启发式：包含大量CJK字符的块
        """
        cjk_blocks = []
        
        for block in blocks:
            text = block.get("text", "")
            if not text:
                continue
            
            # 统计CJK字符数量
            cjk_count = sum(
                1 for char in text
                if (
                    0x4E00 <= ord(char) <= 0x9FFF  # 中文
                    or 0x3040 <= ord(char) <= 0x309F  # 日文平假名
                    or 0x30A0 <= ord(char) <= 0x30FF  # 日文片假名
                    or 0xAC00 <= ord(char) <= 0xD7AF  # 韩文
                )
            )
            
            # 如果CJK字符占比超过30%，认为是CJK密集块
            if len(text) > 0 and cjk_count / len(text) > 0.3:
                cjk_blocks.append(block)
        
        return cjk_blocks


def parse_pdf_hybrid(
    pdf_path: Path,
    *,
    document_id: str,
    project_id: str,
    lang_in: str,
    lang_out: str,
    use_deep_parsing: bool = True,
) -> dict[str, Any]:
    """
    混合模式解析PDF（便捷函数）
    
    Args:
        pdf_path: PDF文件路径
        document_id: 文档ID
        project_id: 项目ID
        lang_in: 源语言
        lang_out: 目标语言
        use_deep_parsing: 是否启用深度解析
    
    Returns:
        结构化文档JSON
    """
    parser = HybridPDFParser(use_deep_parsing=use_deep_parsing)
    return parser.parse(
        pdf_path,
        document_id=document_id,
        project_id=project_id,
        lang_in=lang_in,
        lang_out=lang_out,
    )

