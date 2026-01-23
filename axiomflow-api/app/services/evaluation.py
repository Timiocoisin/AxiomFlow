from __future__ import annotations

"""
评测与回归工具模块

目标：
- 为翻译与版式处理提供统一的离线评测接口；
- 支持 BLEU（优先使用 sacrebleu）、简单术语一致性率、基础版式还原指标；
- 设计为可选依赖：缺少第三方库时自动回退到简化实现，而不会影响主流程。

用法示例（在独立脚本或测试中）::

    from app.services.evaluation import (
        compute_bleu_score,
        compute_term_consistency_score,
        compute_layout_fidelity,
    )

    bleu = compute_bleu_score(refs, hyps)
    term_score = compute_term_consistency_score(pairs, glossary=my_glossary)
    layout_score = compute_layout_fidelity(src_structured, parsed_structured)
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence, Tuple

logger = logging.getLogger(__name__)


# ---- 可选：sacrebleu 用于标准 BLEU 计算 ----

try:  # pragma: no cover - 依赖可能不存在，运行环境决定
    import sacrebleu  # type: ignore[import]

    _SACREBLEU_AVAILABLE = True
except Exception:  # noqa: BLE001
    sacrebleu = None  # type: ignore[assignment]
    _SACREBLEU_AVAILABLE = False


# ---- 通用评测数据结构 ----


@dataclass
class MetricResult:
    name: str
    score: float
    details: Dict[str, Any] | None = None


# ---- BLEU 评测 ----


def _simple_unigram_bleu(
    references: Sequence[str],
    hypotheses: Sequence[str],
) -> float:
    """
    简化版 BLEU（仅基于 unigram 准确率），用于 sacrebleu 不可用时的回退。
    """
    if not references or not hypotheses or len(references) != len(hypotheses):
        return 0.0

    total_overlap = 0
    total_tokens = 0

    for ref, hyp in zip(references, hypotheses):
        ref_tokens = ref.split()
        hyp_tokens = hyp.split()
        total_tokens += max(len(hyp_tokens), 1)

        ref_counts: Dict[str, int] = {}
        for t in ref_tokens:
            ref_counts[t] = ref_counts.get(t, 0) + 1

        overlap = 0
        for t in hyp_tokens:
            if ref_counts.get(t, 0) > 0:
                overlap += 1
                ref_counts[t] -= 1

        total_overlap += overlap

    return total_overlap / max(total_tokens, 1)


def compute_bleu_score(
    references: Sequence[str],
    hypotheses: Sequence[str],
    *,
    tokenize: str = "13a",
) -> MetricResult:
    """
    计算 BLEU 分数。

    优先使用 sacrebleu；若未安装，则回退到简单 unigram 精度。
    """
    if not references or not hypotheses:
        return MetricResult(name="bleu", score=0.0, details={"error": "empty input"})
    if len(references) != len(hypotheses):
        return MetricResult(
            name="bleu",
            score=0.0,
            details={"error": "references and hypotheses length mismatch"},
        )

    if _SACREBLEU_AVAILABLE:  # pragma: no cover - 依赖存在时走此路径
        try:
            # sacrebleu 期望 refs: List[List[str]]
            bleu = sacrebleu.corpus_bleu(hypotheses, [list(references)])  # type: ignore[arg-type]
            return MetricResult(
                name="bleu",
                score=float(bleu.score),
                details={
                    "bp": float(bleu.bp),
                    "counts": bleu.counts,
                    "totals": bleu.totals,
                    "sys_len": int(bleu.sys_len),
                    "ref_len": int(bleu.ref_len),
                    "tokenize": tokenize,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("sacrebleu 计算失败，回退到简化 BLEU: %s", exc)

    # 回退：unigram 精度 * 100 近似为 BLEU
    simple = _simple_unigram_bleu(references, hypotheses)
    return MetricResult(
        name="bleu",
        score=float(simple * 100.0),
        details={"approximation": "unigram_precision"},
    )


# ---- 术语一致性评测 ----


def compute_term_consistency_score(
    pairs: Sequence[Tuple[str, str]],
    *,
    glossary: Dict[str, str] | None = None,
    min_term_length: int = 3,
) -> MetricResult:
    """
    计算术语一致性指标：给定 (source, translation) 对和一个术语表，统计术语在译文中是否被正确使用。

    指标定义：
    - 遍历每个 (src, hyp)：
      - 对于 glossary 中的每个术语 term，若 term (大小写不敏感) 出现在 src 中，
        则认为当前句子有一次“术语机会”；
      - 若对应统一译文在 hyp 中出现（粗略字符串匹配），则计为一次“正确使用”。
    - term_consistency = correct_occurrences / total_opportunities
    """
    if not glossary:
        return MetricResult(
            name="term_consistency",
            score=0.0,
            details={"error": "empty glossary"},
        )

    total_opportunities = 0
    correct_occurrences = 0

    for src, hyp in pairs:
        src_norm = (src or "").lower()
        hyp_text = hyp or ""

        for term, target in glossary.items():
            if not term or not target:
                continue

            term_norm = term.lower()
            if len(term_norm) < min_term_length:
                continue

            if term_norm in src_norm:
                total_opportunities += 1
                if target in hyp_text:
                    correct_occurrences += 1

    if total_opportunities == 0:
        return MetricResult(
            name="term_consistency",
            score=0.0,
            details={"warning": "no term opportunities found"},
        )

    score = correct_occurrences / total_opportunities
    return MetricResult(
        name="term_consistency",
        score=float(score * 100.0),
        details={
            "correct": correct_occurrences,
            "total": total_opportunities,
        },
    )


# ---- 版式还原指标（结构级别） ----


def _count_block_types(pages: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for page in pages:
        for blk in page.get("blocks", []):
            t = (blk.get("type") or "paragraph").lower()
            counts[t] = counts.get(t, 0) + 1
    return counts


def _count_flags(pages: Iterable[Dict[str, Any]], flag: str) -> int:
    total = 0
    for page in pages:
        for blk in page.get("blocks", []):
            if blk.get(flag):
                total += 1
    return total


def compute_layout_fidelity(
    src_structured: Dict[str, Any],
    parsed_structured: Dict[str, Any],
) -> MetricResult:
    """
    粗粒度版式还原指标，用于评估解析/重建后的结构与原文结构的接近程度。

    假设：
    - src_structured / parsed_structured 都是 `parse_pdf_to_structured_json` 的输出形式；
    - 我们主要衡量：
        - 块总数比率；
        - 各 block.type 的分布差异（按比例比较）；
        - header/footer/footnote 标记数量是否接近。
    """
    src_pages = src_structured.get("pages") or []
    tgt_pages = parsed_structured.get("pages") or []

    if not src_pages or not tgt_pages:
        return MetricResult(
            name="layout_fidelity",
            score=0.0,
            details={"error": "empty pages"},
        )

    # 1) 块数量比率
    src_blocks = sum(len(p.get("blocks", [])) for p in src_pages)
    tgt_blocks = sum(len(p.get("blocks", [])) for p in tgt_pages)
    block_count_ratio = tgt_blocks / src_blocks if src_blocks > 0 else 0.0

    # 2) block.type 分布余弦相似度（简单衡量分布是否接近）
    src_type_counts = _count_block_types(src_pages)
    tgt_type_counts = _count_block_types(tgt_pages)

    all_types = sorted(set(src_type_counts) | set(tgt_type_counts))
    src_vec = [src_type_counts.get(t, 0) for t in all_types]
    tgt_vec = [tgt_type_counts.get(t, 0) for t in all_types]

    # 计算余弦相似度
    def _cosine(a: List[int], b: List[int]) -> float:
        import math

        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(y * y for y in b)) or 1.0
        return dot / (na * nb)

    type_cosine = _cosine(src_vec, tgt_vec)

    # 3) header/footer/footnote 标记数量比率
    src_headers = _count_flags(src_pages, "is_header_footer")
    tgt_headers = _count_flags(tgt_pages, "is_header_footer")
    header_ratio = tgt_headers / src_headers if src_headers > 0 else 0.0

    src_footnotes = _count_flags(src_pages, "is_footnote")
    tgt_footnotes = _count_flags(tgt_pages, "is_footnote")
    footnote_ratio = tgt_footnotes / src_footnotes if src_footnotes > 0 else 0.0

    # 汇总一个简单的综合得分（可根据需要调整权重）
    # 这里示例：type 分布相似度 50%，块数量比率 25%，脚注/页眉页脚 25%（平均）
    header_footnote_ratio = (header_ratio + footnote_ratio) / 2 if (src_headers + src_footnotes) > 0 else 1.0
    composite = 0.5 * type_cosine + 0.25 * min(block_count_ratio, 1.0) + 0.25 * min(
        header_footnote_ratio, 1.0
    )

    return MetricResult(
        name="layout_fidelity",
        score=float(composite * 100.0),
        details={
            "block_count_src": src_blocks,
            "block_count_tgt": tgt_blocks,
            "block_count_ratio": block_count_ratio,
            "type_cosine": type_cosine,
            "header_count_src": src_headers,
            "header_count_tgt": tgt_headers,
            "header_ratio": header_ratio,
            "footnote_count_src": src_footnotes,
            "footnote_count_tgt": tgt_footnotes,
            "footnote_ratio": footnote_ratio,
        },
    )



