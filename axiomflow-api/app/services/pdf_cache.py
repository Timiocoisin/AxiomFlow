"""
PDF 解析缓存系统

基于文件哈希的PDF解析结果缓存，显著提升重复解析性能。
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from ..core.observability import counter

logger = logging.getLogger(__name__)

PDF_PARSE_CACHE_HIT = counter(
    "axiomflow_pdf_parse_cache_hit_total",
    "PDF parse cache hits (memory or disk).",
)
PDF_PARSE_CACHE_MISS = counter(
    "axiomflow_pdf_parse_cache_miss_total",
    "PDF parse cache misses.",
)


class PDFParseCache:
    """PDF解析缓存管理器"""

    def __init__(self, cache_dir: Path | None = None):
        """
        Args:
            cache_dir: 缓存目录路径（默认为 None，使用内存缓存）
        """
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.use_disk_cache = True
        else:
            self.use_disk_cache = False
        
        # 内存缓存（快速访问）
        self.memory_cache: dict[str, dict[str, Any]] = {}
        self.max_memory_cache_size = 100  # 最多缓存100个解析结果

    def _compute_file_hash(self, pdf_path: Path, *, chunk_size: int = 8192) -> str:
        """
        计算PDF文件的SHA256哈希值

        Args:
            pdf_path: PDF文件路径
            chunk_size: 读取块大小

        Returns:
            文件的十六进制哈希值
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(pdf_path, "rb") as f:
                # 分块读取，避免大文件占用过多内存
                while chunk := f.read(chunk_size):
                    sha256_hash.update(chunk)
        except Exception as e:
            logger.error(f"计算文件哈希失败: {e}")
            raise
        
        return sha256_hash.hexdigest()

    def _get_cache_key(
        self,
        pdf_path: Path,
        *,
        use_hybrid_parser: bool,
        use_feature_based_layout: bool,
        vfont: str = "",
        vchar: str = "",
    ) -> str:
        """
        生成缓存键

        Args:
            pdf_path: PDF文件路径
            use_hybrid_parser: 是否使用混合解析器
            use_feature_based_layout: 是否使用基于特征的布局检测
            vfont: 公式字体匹配正则
            vchar: 公式字符匹配正则

        Returns:
            缓存键字符串
        """
        file_hash = self._compute_file_hash(pdf_path)
        # 包含解析参数，确保参数变化时缓存失效
        params = {
            "hybrid": use_hybrid_parser,
            "feature_layout": use_feature_based_layout,
            "vfont": vfont,
            "vchar": vchar,
        }
        params_str = json.dumps(params, sort_keys=True, separators=(",", ":"))
        return f"pdf_parse:{file_hash}:{hashlib.sha256(params_str.encode()).hexdigest()}"

    def _get_cache_path(self, cache_key: str) -> Path:
        """获取磁盘缓存文件路径"""
        if not self.cache_dir:
            raise RuntimeError("缓存目录未设置")
        return self.cache_dir / f"{cache_key}.json"

    def get(
        self,
        pdf_path: Path,
        *,
        use_hybrid_parser: bool,
        use_feature_based_layout: bool,
        vfont: str = "",
        vchar: str = "",
    ) -> dict[str, Any] | None:
        """
        获取缓存的解析结果

        Args:
            pdf_path: PDF文件路径
            其他参数: 解析参数（用于生成缓存键）

        Returns:
            缓存的解析结果，如果不存在则返回 None
        """
        cache_key = self._get_cache_key(
            pdf_path,
            use_hybrid_parser=use_hybrid_parser,
            use_feature_based_layout=use_feature_based_layout,
            vfont=vfont,
            vchar=vchar,
        )

        # 先检查内存缓存
        if cache_key in self.memory_cache:
            logger.debug(f"从内存缓存获取PDF解析结果: {pdf_path.name}")
            try:
                PDF_PARSE_CACHE_HIT.inc()
            except Exception:
                pass
            return self.memory_cache[cache_key]

        # 检查磁盘缓存
        if self.use_disk_cache:
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        result = json.load(f)
                    logger.debug(f"从磁盘缓存获取PDF解析结果: {pdf_path.name}")
                    try:
                        PDF_PARSE_CACHE_HIT.inc()
                    except Exception:
                        pass
                    
                    # 添加到内存缓存（如果还有空间）
                    if len(self.memory_cache) < self.max_memory_cache_size:
                        self.memory_cache[cache_key] = result
                    
                    return result
                except Exception as e:
                    logger.warning(f"读取磁盘缓存失败: {e}")

        try:
            PDF_PARSE_CACHE_MISS.inc()
        except Exception:
            pass
        return None

    def set(
        self,
        pdf_path: Path,
        result: dict[str, Any],
        *,
        use_hybrid_parser: bool,
        use_feature_based_layout: bool,
        vfont: str = "",
        vchar: str = "",
    ) -> None:
        """
        保存解析结果到缓存

        Args:
            pdf_path: PDF文件路径
            result: 解析结果
            其他参数: 解析参数（用于生成缓存键）
        """
        cache_key = self._get_cache_key(
            pdf_path,
            use_hybrid_parser=use_hybrid_parser,
            use_feature_based_layout=use_feature_based_layout,
            vfont=vfont,
            vchar=vchar,
        )

        # 保存到内存缓存
        if len(self.memory_cache) >= self.max_memory_cache_size:
            # 简单策略：删除第一个（FIFO）
            first_key = next(iter(self.memory_cache))
            del self.memory_cache[first_key]
        
        self.memory_cache[cache_key] = result

        # 保存到磁盘缓存
        if self.use_disk_cache:
            cache_path = self._get_cache_path(cache_key)
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logger.debug(f"PDF解析结果已缓存到磁盘: {pdf_path.name}")
            except Exception as e:
                logger.warning(f"保存磁盘缓存失败: {e}")

    def clear(self) -> None:
        """清空所有缓存"""
        self.memory_cache.clear()
        if self.use_disk_cache and self.cache_dir:
            try:
                for cache_file in self.cache_dir.glob("pdf_parse:*.json"):
                    cache_file.unlink()
                logger.info("PDF解析缓存已清空")
            except Exception as e:
                logger.warning(f"清空磁盘缓存失败: {e}")


# 全局缓存实例（单例模式）
_global_cache: PDFParseCache | None = None


def get_pdf_parse_cache(cache_dir: Path | None = None) -> PDFParseCache:
    """
    获取PDF解析缓存实例（单例）

    Args:
        cache_dir: 缓存目录（仅在首次调用时生效，如果为 None 则从 .env 读取）

    Returns:
        PDFParseCache 实例
    """
    global _global_cache
    if _global_cache is None:
        if cache_dir is None:
            # 从 Settings 读取缓存目录（.env 驱动）
            try:
                from ..core.config import settings

                if not getattr(settings, "pdf_cache_enabled", True):
                    cache_dir = None
                else:
                    if getattr(settings, "pdf_parse_cache_dir", ""):
                        cache_dir = Path(settings.pdf_parse_cache_dir)
                    elif getattr(settings, "cache_dir", ""):
                        cache_dir = Path(settings.cache_dir) / "pdf_parse"

                    if cache_dir is not None:
                        cache_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                cache_dir = None

        # 创建缓存实例
        if cache_dir is None:
            _global_cache = PDFParseCache()  # 仅内存缓存
        else:
            _global_cache = PDFParseCache(cache_dir)  # 磁盘 + 内存缓存
    return _global_cache

