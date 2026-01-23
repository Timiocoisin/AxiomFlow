from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256
import json


@dataclass(frozen=True)
class TranslateMeta:
    lang_in: str
    lang_out: str
    document_id: str | None = None
    block_type: str | None = None
    glossary: dict[str, str] | None = None


class BaseProvider(ABC):
    """
    翻译 Provider 抽象层：屏蔽不同服务（云端/本地/传统MT）的调用细节。
    编排器负责分批、上下文、术语、记忆等；Provider 只做最小的“输入->输出”翻译。

    这里实现了一个简单的进程内 KV 缓存，按 lang_in/lang_out/model/text 维度区分。
    """

    name: str = "base"

    def __init__(self) -> None:
        # 进程内缓存：key -> translated_text
        self._cache: dict[str, str] = {}

    def _cache_key(self, text: str, meta: TranslateMeta) -> str:
        h = sha256(text.encode("utf-8")).hexdigest()
        glossary_hash = ""
        if meta.glossary:
            g = json.dumps(meta.glossary, ensure_ascii=False, sort_keys=True)
            glossary_hash = sha256(g.encode("utf-8")).hexdigest()
        return f"{self.name}|{meta.lang_in}|{meta.lang_out}|{glossary_hash}|{h}"

    async def translate(self, text: str, meta: TranslateMeta, ignore_cache: bool = False) -> str:
        key = self._cache_key(text, meta)
        if not ignore_cache and key in self._cache:
            return self._cache[key]
        translated = await self._translate_impl(text, meta)
        self._cache[key] = translated
        return translated

    @abstractmethod
    async def _translate_impl(self, text: str, meta: TranslateMeta) -> str:
        raise NotImplementedError

