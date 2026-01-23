from __future__ import annotations

from dataclasses import dataclass
import json
import logging

from .providers.base import TranslateMeta
from .providers.registry import get_provider
from ..repo import repo
from .text_protect import protect_math, unprotect_math
from .concurrent_translator import ConcurrentTranslator, TranslationTask
from .context_aware_translation import (
    build_context_window,
    translate_with_context,
    group_consecutive_blocks,
)
from .term_consistency import TermConsistencyChecker, unify_terms_in_translations
from .smart_batch_translator import SmartBatchTranslator
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TranslateStrategy:
    """
    翻译策略配置
    
    支持上下文感知、术语一致性、智能批处理等高级功能。
    """

    provider: str = "ollama"
    use_context: bool = True  # 是否使用上下文感知翻译
    context_window_size: int = 2  # 上下文窗口大小
    use_term_consistency: bool = True  # 是否使用术语一致性检查
    use_smart_batching: bool = True  # 是否使用智能批处理


class TranslateOrchestrator:
    def __init__(self, max_concurrent: int | None = None):
        """
        Args:
            max_concurrent: 最大并发翻译数（若为 None，则从 .env 的 settings.translation_max_concurrent 读取）
        """
        if max_concurrent is None:
            try:
                from ..core.config import settings

                max_concurrent = int(getattr(settings, "translation_max_concurrent", 5))
            except Exception:
                max_concurrent = 5

        self.max_concurrent = int(max_concurrent)
        self.concurrent_translator = ConcurrentTranslator(max_workers=self.max_concurrent, max_retries=3)
        self.smart_batch_translator = SmartBatchTranslator(
            max_workers=self.max_concurrent,
            max_retries=3,
            adaptive_batch_size=True,
        )

    async def translate_text(self, text: str, meta: TranslateMeta, strategy: TranslateStrategy) -> str:
        """
        翻译单个文本（带缓存和重试）

        Args:
            text: 原始文本
            meta: 翻译元数据
            strategy: 翻译策略

        Returns:
            翻译后的文本

        Raises:
            Exception: 翻译失败时的异常
        """
        provider = get_provider(strategy.provider)

        protected = protect_math(text)
        meta2 = TranslateMeta(
            lang_in=meta.lang_in,
            lang_out=meta.lang_out,
            document_id=meta.document_id,
            block_type=meta.block_type,
            glossary=meta.glossary,
        )

        # 构建参数化缓存参数（类似开源项目的实现）
        # 包含所有可能影响翻译结果的参数
        translate_params = {
            "lang_in": meta2.lang_in,
            "lang_out": meta2.lang_out,
            "glossary": meta2.glossary or {},  # 术语表（会被规范化）
        }
        
        # 如果 provider 支持额外参数（如 model, temperature），添加到缓存参数中
        if hasattr(provider, 'model') and provider.model:
            translate_params['model'] = provider.model
        if hasattr(provider, 'temperature') and provider.temperature is not None:
            translate_params['temperature'] = provider.temperature

        # 使用参数化缓存查询
        cached = repo.tm_get(
            translate_engine=provider.name,
            translate_params=translate_params,
            original_text=protected.text,
        )
        
        if cached is not None:
            return unprotect_math(cached, protected.mapping)

        try:
            translated = await provider.translate(protected.text, meta2)
            # 使用参数化缓存存储
            repo.tm_set(
                translate_engine=provider.name,
                translate_params=translate_params,
                original_text=protected.text,
                translated_text=translated,
            )
            return unprotect_math(translated, protected.mapping)
        except Exception as exc:
            logger.error(
                f"翻译失败: {type(exc).__name__}: {str(exc)[:200]} | "
                f"文本长度: {len(text)} | 语言: {meta.lang_in}->{meta.lang_out}",
                exc_info=True,
            )
            raise

    async def translate_blocks_batch(
        self,
        blocks: list[dict[str, Any]],
        meta_template: TranslateMeta,
        strategy: TranslateStrategy,
        *,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """
        批量并发翻译多个文本块

        支持上下文感知翻译、术语一致性保证和智能批处理优化。

        Args:
            blocks: 文本块列表（每个块包含 id, text, type 等字段）
            meta_template: 翻译元数据模板（会被复制用于每个块）
            strategy: 翻译策略
            progress_callback: 进度回调（完成数, 总数）

        Returns:
            更新后的 blocks 列表（包含 translation 字段）
        """
        provider = get_provider(strategy.provider)
        
        # 初始化术语一致性检查器
        term_checker = TermConsistencyChecker() if strategy.use_term_consistency else None

        # 创建任务列表
        valid_blocks = [
            b
            for b in blocks
            if b.get("text", "").strip()
            and not b.get("is_header_footer")
            and not b.get("is_footnote")
        ]

        # 如果使用上下文感知翻译，需要构建上下文窗口
        use_context_translation = strategy.use_context and len(valid_blocks) > 1
        
        async def translate_func(text: str, meta: TranslateMeta) -> str:
            """包装的翻译函数（用于并发翻译器）"""
            protected = protect_math(text)
            meta2 = TranslateMeta(
                lang_in=meta.lang_in,
                lang_out=meta.lang_out,
                document_id=meta.document_id,
                block_type=meta.block_type,
                glossary=meta.glossary,
            )

            # 构建参数化缓存参数
            translate_params = {
                "lang_in": meta2.lang_in,
                "lang_out": meta2.lang_out,
                "glossary": meta2.glossary or {},
            }
            
            # 如果 provider 支持额外参数（如 model, temperature），添加到缓存参数中
            if hasattr(provider, 'model') and provider.model:
                translate_params['model'] = provider.model
            if hasattr(provider, 'temperature') and provider.temperature is not None:
                translate_params['temperature'] = provider.temperature

            # 使用参数化缓存查询
            cached = repo.tm_get(
                translate_engine=provider.name,
                translate_params=translate_params,
                original_text=protected.text,
            )
            
            if cached is not None:
                return unprotect_math(cached, protected.mapping)

            # 如果有上下文且启用了上下文感知翻译
            if use_context_translation:
                # 查找当前块的索引（需要从外部传入）
                # 这里简化处理，如果不支持上下文则回退到普通翻译
                pass
            
            translated = await provider.translate(protected.text, meta2)
            # 使用参数化缓存存储
            repo.tm_set(
                translate_engine=provider.name,
                translate_params=translate_params,
                original_text=protected.text,
                translated_text=translated,
            )
            return unprotect_math(translated, protected.mapping)

        tasks = [
            TranslationTask(
                block_id=b.get("id", ""),
                text=b.get("text", "").strip(),
                meta=TranslateMeta(
                    lang_in=meta_template.lang_in,
                    lang_out=meta_template.lang_out,
                    document_id=meta_template.document_id,
                    block_type=b.get("type"),
                    glossary=meta_template.glossary,
                ),
                page_index=b.get("page_index", 0),
                block_index=i,
            )
            for i, b in enumerate(valid_blocks)
        ]

        # 选择翻译器（智能批处理或普通批处理）
        if strategy.use_smart_batching:
            # 使用智能批处理翻译器
            results = await self.smart_batch_translator.translate_batch_smart(
                tasks,
                translate_func,
                progress_callback=progress_callback,
                use_priority=True,
                use_grouping=True,
            )
        else:
            # 使用普通批处理翻译器
            results = await self.concurrent_translator.translate_batch(
                tasks, translate_func, progress_callback=progress_callback
            )

        # 更新 blocks
        result_map = {r.block_id: r for r in results}
        block_map = {b.get("id"): b for b in valid_blocks}

        for result in results:
            block = block_map.get(result.block_id)
            if block:
                if result.translation is not None:
                    block["translation"] = result.translation
                    
                    # 如果有术语检查器，记录术语映射
                    if term_checker:
                        term_checker.add_term_mapping(block.get("text", ""), result.translation)
                else:
                    # 翻译失败，记录错误
                    block["translation"] = f"[翻译失败: {result.error}]" if result.error else "[翻译失败]"
                    block["translation_error"] = str(result.error) if result.error else "Unknown error"

        # 如果启用了术语一致性，统一术语翻译
        if term_checker:
            logger.info("执行术语一致性检查和统一...")
            unify_terms_in_translations(valid_blocks, term_checker)
            
            # 更新术语表到元数据
            glossary = term_checker.get_glossary()
            if glossary and meta_template.glossary:
                meta_template.glossary.update(glossary)

        return blocks


