from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ProtectedText:
    text: str
    mapping: dict[str, str]  # placeholder -> original


_PATTERNS = [
    # display math $$...$$
    re.compile(r"\$\$[\s\S]+?\$\$"),
    # inline math $...$ (avoid $$...$$ by negative lookahead/lookbehind)
    re.compile(r"(?<!\$)\$[^$\n]+?\$(?!\$)"),
    # \( ... \)
    re.compile(r"\\\([\s\S]+?\\\)"),
    # \[ ... \]
    re.compile(r"\\\[[\s\S]+?\\\]"),
]


def protect_math(text: str) -> ProtectedText:
    """
    把 LaTeX/数学片段替换为占位符 {v1}、{v2}…，翻译完成后再回填，减少被模型改写的概率。
    """
    mapping: dict[str, str] = {}
    out = text
    idx = 1

    # 为了避免占位符被重复替换，采用一次遍历搜集所有片段（按出现顺序）后再替换
    spans: list[tuple[int, int, str]] = []
    for pat in _PATTERNS:
        for m in pat.finditer(text):
            spans.append((m.start(), m.end(), m.group(0)))
    spans.sort(key=lambda x: (x[0], -(x[1] - x[0])))

    # 去重/去包含：保留外层更大的片段
    filtered: list[tuple[int, int, str]] = []
    last_end = -1
    for s, e, val in spans:
        if s < last_end:
            continue
        filtered.append((s, e, val))
        last_end = e

    if not filtered:
        return ProtectedText(text=text, mapping={})

    # 逆序替换，避免索引偏移
    for s, e, val in reversed(filtered):
        placeholder = f"{{v{idx}}}"
        idx += 1
        mapping[placeholder] = val
        out = out[:s] + placeholder + out[e:]

    return ProtectedText(text=out, mapping=mapping)


def unprotect_math(text: str, mapping: dict[str, str]) -> str:
    out = text
    # 占位符回填：长度短的先回填容易造成嵌套误替换，所以按 key 长度倒序
    for placeholder in sorted(mapping.keys(), key=len, reverse=True):
        out = out.replace(placeholder, mapping[placeholder])
    return out


