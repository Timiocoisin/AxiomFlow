"""
术语一致性保证模块（增强版）

目标：
- 在不依赖重量级外部 NLP/对齐库的前提下，尽量提升术语抽取和统一精度；
- 聚焦英文技术术语（大写/驼峰/多词名词短语）的一致翻译；
- 为后续接入更强 NLP/对齐模型预留接口。
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# 可选：使用 sentence-transformers 做术语与译文上下文的语义对齐
try:  # 轻量集成，依赖不存在时自动回退到纯统计
    from sentence_transformers import SentenceTransformer  # type: ignore[import]
    import numpy as np  # type: ignore[import]

    _EMBEDDING_AVAILABLE = True
except Exception:  # pragma: no cover - 在未安装依赖环境下自然走回退逻辑
    SentenceTransformer = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]
    _EMBEDDING_AVAILABLE = False


_EN_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "which",
    "into",
    "onto",
    "over",
    "under",
    "such",
    "also",
    "using",
    "based",
}


def _normalize_term(term: str) -> str:
    """统一术语规范形式（小写 + 单空格）"""
    term = term.strip()
    term = re.sub(r"\s+", " ", term)
    return term.lower()


def _extract_english_terms(text: str) -> List[str]:
    """
    提取英文候选术语（启发式）：
    - 大写开头的单词/短语：Machine Learning, Deep Neural Network
    - 驼峰词：TransformerEncoder, CrossEntropyLoss
    """
    if not text:
        return []

    candidates: List[str] = []

    # 1) 大写开头的多词名词短语（最多 4 个词）
    phrase_pattern = re.compile(
        r"\b(?:[A-Z][a-zA-Z0-9]+(?:\s+|[-_/])){1,3}[A-Z][a-zA-Z0-9]+\b"
    )
    for m in phrase_pattern.finditer(text):
        candidates.append(m.group(0))

    # 2) 单词级术语：全大写或驼峰
    word_pattern = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b|\b[A-Z]{2,}\b")
    for m in word_pattern.finditer(text):
        candidates.append(m.group(0))

    # 3) 过滤太短/太长以及常见虚词
    results: List[str] = []
    for c in candidates:
        c_stripped = c.strip()
        if len(c_stripped) < 3 or len(c_stripped) > 80:
            continue
        if c_stripped.lower() in _EN_STOPWORDS:
            continue
        results.append(c_stripped)

    return results


class TermConsistencyChecker:
    """
    术语一致性检查器（面向单文档）

    使用方式（与 orchestrator 当前集成兼容）：
    - 每个块翻译完成后调用 add_term_mapping(block_text, translated_text)
    - 所有块翻译结束后，调用 unify_terms_in_translations(...) 统一全篇译文中的术语
    """

    def __init__(self) -> None:
        # 原始术语频次（基于英文候选抽取）
        self.source_terms: Counter[str] = Counter()
        # 原文术语 -> { 译文候选 -> 频次 }（候选一般是英文术语本身或其写法）
        self.term_mappings: Dict[str, Counter[str]] = defaultdict(Counter)
        # 原文术语 -> 出现过的整句译文列表（用于 embedding 对齐）
        self.term_translation_contexts: Dict[str, List[str]] = defaultdict(list)
        # 最终确定的术语表：原文术语（规范形式）-> 统一译文（短语，或回退为英文）
        self.final_glossary: Dict[str, str] = {}

        # 延迟加载的嵌入模型
        self._embedder: Any | None = None

    # -------- 内部：嵌入模型管理 --------

    def _ensure_embedder(self) -> None:
        """按需加载 sentence-transformers 模型，未安装时保持 None。"""
        if not _EMBEDDING_AVAILABLE or self._embedder is not None:
            return
        try:
            # 选一个通用多语种小模型即可，兼顾质量与性能
            self._embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")  # type: ignore[call-arg]
            logger.info("TermConsistencyChecker: 已加载 sentence-transformers 嵌入模型")
        except Exception as exc:  # pragma: no cover - 运行时环境差异
            logger.warning("加载 sentence-transformers 失败，将回退到纯统计术语对齐: %s", exc)
            self._embedder = None

    def _best_translation_via_embedding(
        self,
        term: str,
        contexts: List[str],
    ) -> str | None:
        """
        使用嵌入在多个整句译文中为术语选择“最语义相关的一句”，
        后续可以从该句中再抽取短语；当前直接返回整句作为统一译文候选。
        """
        if not contexts:
            return None

        self._ensure_embedder()
        if self._embedder is None or not _EMBEDDING_AVAILABLE:  # 未安装依赖或加载失败
            return None

        try:
            # term 向量 & 各译文上下文向量
            term_vec = self._embedder.encode([term])[0]  # type: ignore[operator]
            ctx_vecs = self._embedder.encode(contexts)  # type: ignore[operator]

            term_vec = np.asarray(term_vec)
            ctx_vecs = np.asarray(ctx_vecs)

            # 余弦相似度
            term_norm = np.linalg.norm(term_vec) + 1e-8
            ctx_norms = np.linalg.norm(ctx_vecs, axis=1) + 1e-8
            sims = (ctx_vecs @ term_vec) / (ctx_norms * term_norm)

            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])

            # 设一个保守阈值，避免噪声：例如 0.3
            if best_sim < 0.3:
                return None

            return contexts[best_idx]
        except Exception as exc:  # pragma: no cover - 安全兜底
            logger.warning(
                "术语嵌入对齐失败，将回退到频次策略: term=%s, error=%s", term, exc
            )
            return None

    # -------- 抽取与统计 --------

    def extract_and_count_terms(self, text: str) -> None:
        """
        从原文块中抽取候选术语并累计频次。
        目前主要针对英文技术术语（大写/驼峰/多词短语）。
        """
        for term in _extract_english_terms(text):
            key = _normalize_term(term)
            self.source_terms[key] += 1

    def add_term_mapping(self, source_text: str, translated_text: str) -> None:
        """
        从一对 (原文块, 译文块) 中抽取候选术语并记录粗略对齐。

        注意：
        - 这里不做复杂的词级对齐，只记录“该术语对应的译文片段候选”，
          当前实现主要用于确保英文术语在译文中保持统一（英文 > 英文）。
        """
        if not source_text or not translated_text:
            return

        # 先更新原文术语频次
        self.extract_and_count_terms(source_text)

        # 简单对齐策略：
        # - 若原文术语在译文中也出现（大小写不敏感），则认为“保留英文术语”为候选译文；
        # - 否则，暂时不尝试自动猜测中文译文，后续可以升级为相似度/对齐模型。
        lowered_translation = translated_text.lower()

        for term in _extract_english_terms(source_text):
            key = _normalize_term(term)
            if not key:
                continue

            # 只在术语本身出现多次的情况下，才考虑进入最终术语表
            self.source_terms[key] += 0  # 确保键存在

            # 记录整句译文上下文（后续做 embedding 对齐用）
            if translated_text not in self.term_translation_contexts[key]:
                self.term_translation_contexts[key].append(translated_text)

            if key in lowered_translation:
                # 候选译文：直接使用英文原词（保持英文术语不被随机翻译）
                self.term_mappings[key][term] += 1

    # -------- 术语表生成 --------

    def determine_final_glossary(self, min_frequency: int = 2) -> Dict[str, str]:
        """
        根据目前收集到的统计信息，生成最终术语表。

        策略：
        - 仅保留在文档中出现次数 >= min_frequency 的术语；
        - 若有多个候选译文，选择出现频次最高的一个；
        - 若没有可用译文候选，则保留原文（统一使用英文术语）。
        """
        final: Dict[str, str] = {}

        for src_term, freq in self.source_terms.items():
            if freq < min_frequency:
                continue

            mapping = self.term_mappings.get(src_term)
            contexts = self.term_translation_contexts.get(src_term, [])

            best_translation: str | None = None

            # 1) 首选：若启用了嵌入且能从多个译文上下文中选出一个最相关的句子，则用它
            embed_choice = self._best_translation_via_embedding(src_term, contexts)
            if embed_choice:
                best_translation = embed_choice.strip()

            # 2) 次选：若有候选译文写法（通常是英文术语本身的不同大小写），按频次选最高
            if not best_translation and mapping and len(mapping) > 0:
                best_translation = mapping.most_common(1)[0][0]

            # 3) 兜底：保持英文术语本身
            if not best_translation:
                best_translation = src_term

            final[src_term] = best_translation

        self.final_glossary = final
        logger.info("术语表生成完成：%d 项", len(final))
        return final

    def get_glossary(self) -> Dict[str, str]:
        """获取当前确定的术语表（若尚未生成，则先生成一次）。"""
        if not self.final_glossary and self.source_terms:
            self.determine_final_glossary()
        return dict(self.final_glossary)


def _replace_term_in_translation(text: str, term: str, unified_translation: str) -> str:
    """
    在译文中用更安全的方式替换术语：
    - 对英文术语使用大小写不敏感 + 词边界；
    - 避免误替换到其他词的一部分。
    """
    if not text or not term or not unified_translation:
        return text

    # 英文术语：使用 \b 词边界（对纯 ASCII 有效）
    if re.match(r"^[A-Za-z0-9 _\-/]+$", term):
        pattern = r"\b" + re.escape(term) + r"\b"
        return re.sub(pattern, unified_translation, text, flags=re.IGNORECASE)

    # 其它情况（例如混合符号），退化为简单替换（风险较小的场景）
    return text.replace(term, unified_translation)


def unify_terms_in_translations(
    blocks: List[Dict[str, Any]],
    checker: TermConsistencyChecker,
) -> None:
    """
    根据 TermConsistencyChecker 中收集的信息，统一整篇文档中的术语翻译。

    当前策略：
    - 面向英文术语：确保相同英文术语在所有译文中保持统一形态；
    - 后续若接入双语对齐模型，可扩展为“英文术语 -> 中文术语”的强制统一。
    """
    if not blocks:
        return

    # 确保已经生成术语表
    glossary = checker.get_glossary()
    if not glossary:
        return

    for block in blocks:
        translation = block.get("translation", "")
        if not translation:
            continue

        original_translation = translation

        for src_term, unified in glossary.items():
            # src_term 是规范化后的 key，需要恢复一个可见形式；
            # 这里直接使用 unified 作为目标形式：
            translation = _replace_term_in_translation(translation, src_term, unified)

        if translation != original_translation:
            block["translation"] = translation
            block["term_unified"] = True
