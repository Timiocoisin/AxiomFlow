from __future__ import annotations

import html
import logging
import re
import unicodedata
from typing import Any

import requests

from .base import BaseProvider, TranslateMeta

logger = logging.getLogger(__name__)


def remove_control_characters(s: str) -> str:
    """移除控制字符"""
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")


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
        self.session = requests.Session()
        self.endpoint = "https://translate.google.com/m"
        self.headers = {
            "User-Agent": "Mozilla/4.0 (compatible;MSIE 6.0;Windows NT 5.1;SV1;.NET CLR 1.1.4322;.NET CLR 2.0.50727;.NET CLR 3.0.04506.30)"
        }
        logger.info("GoogleProvider initialized")

    def _normalize_lang(self, lang: str) -> str:
        """
        标准化语言代码（Google 翻译使用 zh-CN 而不是 zh）
        """
        lang_map = {"zh": "zh-CN", "zh-Hans": "zh-CN", "zh-Hant": "zh-TW"}
        return lang_map.get(lang.lower(), lang)

    async def _translate_impl(self, text: str, meta: TranslateMeta) -> str:
        """
        实现 Google 翻译
        """
        if not text or not text.strip():
            return text

        # Google 翻译最大长度限制
        text = text[:5000]

        try:
            lang_in = self._normalize_lang(meta.lang_in)
            lang_out = self._normalize_lang(meta.lang_out)

            response = self.session.get(
                self.endpoint,
                params={"tl": lang_out, "sl": lang_in, "q": text},
                headers=self.headers,
                timeout=10,
            )

            if response.status_code == 400:
                logger.error(f"Google translate returned 400 for text: {text[:100]}")
                return "IRREPARABLE TRANSLATION ERROR"

            response.raise_for_status()

            # 从 HTML 中提取翻译结果
            re_result = re.findall(
                r'(?s)class="(?:t0|result-container)">(.*?)<', response.text
            )

            if not re_result:
                logger.warning(f"No translation result found for text: {text[:100]}")
                return text  # 返回原文作为回退

            result = html.unescape(re_result[0])
            result = remove_control_characters(result)

            if not result or result.strip() == "":
                logger.warning(f"Empty translation result for text: {text[:100]}")
                return text  # 返回原文作为回退

            return result

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Google translate request failed: {type(e).__name__}: {str(e)} | "
                f"text length: {len(text)} | lang: {meta.lang_in}->{meta.lang_out}",
                exc_info=True,
            )
            # 网络错误时返回原文，避免整个翻译任务失败
            return text
        except Exception as e:
            logger.error(
                f"Google translate failed: {type(e).__name__}: {str(e)} | "
                f"text length: {len(text)} | lang: {meta.lang_in}->{meta.lang_out}",
                exc_info=True,
            )
            raise

