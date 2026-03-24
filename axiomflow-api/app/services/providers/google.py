from __future__ import annotations

import logging
from typing import Any

from googletrans import Translator

from .base import BaseProvider, TranslateMeta

logger = logging.getLogger(__name__)


class GoogleProvider(BaseProvider):
    """
    Google 翻译 Provider（免费，无需 API Key）

    特点：
    - 免费使用，无需配置
    - 支持多种语言
    - 适合快速翻译场景

    注意：
    - 单次翻译最大长度 5000 字符
    - 使用 Google 翻译网页版接口
    """

    name = "google"

    def __init__(self) -> None:
        super().__init__()
        # 按照 test.py 的方式使用 googletrans 的 Translator
        # 注意：googletrans 本身是同步接口，这里简单按文档示例用 await 调用，
        # 若内部返回协程对象则可以直接 await；否则将结果视为同步返回。
        self.translator = Translator()
        logger.info("GoogleProvider initialized")

    def _normalize_lang(self, lang: str) -> str:
        """标准化语言代码（Google 翻译使用 zh-CN 而不是 zh）"""
        lang_map = {"zh": "zh-CN", "zh-Hans": "zh-CN", "zh-Hant": "zh-TW"}
        return lang_map.get(lang.lower(), lang)

    async def _translate_impl(self, text: str, meta: TranslateMeta) -> str:
        """实现 Google 翻译（参照 test.py 的用法）"""
        if not text or not text.strip():
            return text

        try:
            lang_in = self._normalize_lang(meta.lang_in)
            lang_out = self._normalize_lang(meta.lang_out)

            # googletrans 典型调用方式：
            # translation = await translator.translate('text', dest='zh-CN')
            # 这里直接按 test.py 的写法调用
            translation: Any = await self.translator.translate(
                text, dest=lang_out, src=lang_in
            )

        except TypeError:
            # 某些版本下 translate 是同步函数，await 会抛 TypeError，这里退回同步调用
            translation = self.translator.translate(text, dest=lang_out, src=lang_in)  # type: ignore[assignment]
        except Exception as e:
            logger.error(
                f"Google translate failed (request error): {type(e).__name__}: {str(e)} | "
                f"text length: {len(text)} | lang: {meta.lang_in}->{meta.lang_out}",
                exc_info=True,
            )
            # 任何异常时先回退到原文，避免整段丢失
            return text

        try:
            result = getattr(translation, "text", None)
            if not isinstance(result, str) or not result.strip():
                logger.warning(
                    f"Empty translation result from googletrans for text: {text[:100]}"
                )
                return text

            # ---- 问号占比检测：如果翻译结果大部分是“？”则认为翻译失败，回退原文 ----
            if result:
                total_len = len(result)
                q_count = result.count("?")
                if total_len > 0 and q_count / total_len > 0.5:
                    logger.warning(
                        "googletrans returned suspicious result (too many '?'), "
                        f"len={total_len}, q_count={q_count}, sample_in={text[:80]!r}, "
                        f"sample_out={result[:80]!r}. Fallback to source text."
                    )
                    return text

            return result
        except Exception as e:
            logger.error(
                f"Google translate failed (post-process): {type(e).__name__}: {str(e)} | "
                f"text length: {len(text)} | lang: {meta.lang_in}->{meta.lang_out}",
                exc_info=True,
            )
            # 最终兜底：返回原文
            return text

