from __future__ import annotations

"""
语言检测与简单领域识别

为了避免重依赖，这里采用：
- 优先使用 langdetect（如已安装）做通用语言检测；
- 否则使用基于 Unicode 范围的简易启发式（中/英/其它）。
"""

from typing import Literal
import logging

logger = logging.getLogger(__name__)

try:
    from langdetect import detect  # type: ignore

    LANG_DETECT_AVAILABLE = True
except Exception:  # pragma: no cover
    detect = None  # type: ignore
    LANG_DETECT_AVAILABLE = False


LanguageCode = Literal["zh", "en", "ja", "ko", "fr", "de", "es", "unknown"]
DomainLabel = Literal["academic", "legal", "general"]


def _heuristic_detect(text: str) -> LanguageCode:
    """基于字符分布的简单语言识别（备用方案）"""
    text = (text or "").strip()
    if not text:
        return "unknown"

    total = len(text)
    cjk = sum(
        1
        for ch in text
        if 0x4E00 <= ord(ch) <= 0x9FFF  # CJK
        or 0x3040 <= ord(ch) <= 0x30FF  # 日文
        or 0xAC00 <= ord(ch) <= 0xD7AF  # 韩文
    )
    latin = sum(1 for ch in text if ("A" <= ch <= "Z") or ("a" <= ch <= "z"))

    if cjk / total > 0.4:
        return "zh"
    if latin / total > 0.4:
        return "en"
    return "unknown"


def detect_language(text: str) -> LanguageCode:
    """检测文本主语言，返回简化语言码。"""
    text = (text or "").strip()
    if not text:
        return "unknown"

    if LANG_DETECT_AVAILABLE:
        try:
            code = detect(text)
            if code.startswith("zh"):
                return "zh"
            if code.startswith("en"):
                return "en"
            if code.startswith("ja"):
                return "ja"
            if code.startswith("ko"):
                return "ko"
            if code.startswith("fr"):
                return "fr"
            if code.startswith("de"):
                return "de"
            if code.startswith("es"):
                return "es"
        except Exception as exc:  # pragma: no cover
            logger.warning("langdetect 语言检测失败，将使用启发式: %s", exc)

    return _heuristic_detect(text)


def guess_domain_from_title(title: str) -> DomainLabel:
    """
    非严格的领域识别：
    - title/文件名里包含 law/contract/judgment 之类视为 legal
    - 否则如果包含 arxiv, conference, journal, proceedings 等视为 academic
    - 其它归 general
    """
    lowered = (title or "").lower()
    if any(k in lowered for k in ["contract", "law", "judgment", "case ", "法规", "合同"]):
        return "legal"
    if any(k in lowered for k in ["arxiv", "conference", "journal", "proceedings", "ieee", "acm"]):
        return "academic"
    return "general"


