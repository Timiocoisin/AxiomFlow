from __future__ import annotations

import re
from collections import Counter

from fastapi import APIRouter

from ..repo import repo

router = APIRouter(prefix="/documents", tags=["terms"])


def _extract_candidate_terms(text: str) -> list[str]:
    # 极简候选词：连续的英文单词（含连字符），长度>=4
    return re.findall(r"\b[A-Za-z][A-Za-z\-]{3,}\b", text)


@router.get("/{document_id}/terms", response_model=dict)
async def suggest_terms(document_id: str, top_k: int = 30) -> dict:
    """
    v1.0 雏形：从全文 blocks 中提取高频英文术语候选（不做NLP，仅启发式）。
    """
    data = repo.load_document_json(document_id)
    counts: Counter[str] = Counter()
    for p in data.get("pages", []):
        for b in p.get("blocks", []):
            if (b.get("type") or "") in ("figure", "table"):
                continue
            for term in _extract_candidate_terms(b.get("text") or ""):
                counts[term] += 1

    top = [{"term": t, "count": c} for t, c in counts.most_common(max(1, min(200, top_k)))]
    return {"document_id": document_id, "terms": top}


