"""
上下文感知翻译模块

提供跨块上下文窗口、相邻块联合翻译等功能，显著提升翻译质量。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .providers.base import TranslateMeta, BaseProvider

logger = logging.getLogger(__name__)


@dataclass
class BlockContext:
    """文本块及其上下文"""

    block_id: str
    text: str
    block_type: str | None
    page_index: int
    block_index: int
    # 上下文信息
    prev_block: dict[str, Any] | None = None  # 前一个块
    next_block: dict[str, Any] | None = None  # 下一个块
    prev_heading: dict[str, Any] | None = None  # 前一个标题
    section_context: list[dict[str, Any]] | None = None  # 当前章节的其他块（用于章节理解）


def build_context_window(
    blocks: list[dict[str, Any]],
    current_index: int,
    *,
    window_size: int = 2,
    include_headings: bool = True,
) -> BlockContext:
    """
    为当前块构建上下文窗口

    Args:
        blocks: 所有文本块列表
        current_index: 当前块的索引
        window_size: 上下文窗口大小（前后各包含多少个块）
        include_headings: 是否包含较远的标题

    Returns:
        BlockContext 对象
    """
    if current_index < 0 or current_index >= len(blocks):
        raise ValueError(f"Invalid block index: {current_index}")

    current_block = blocks[current_index]
    
    # 前一个块
    prev_block = blocks[current_index - 1] if current_index > 0 else None
    
    # 后一个块
    next_block = (
        blocks[current_index + 1] if current_index < len(blocks) - 1 else None
    )

    # 查找前一个标题
    prev_heading = None
    if include_headings:
        for i in range(current_index - 1, -1, -1):
            block = blocks[i]
            if block.get("type") == "heading" or block.get("type") == "title":
                prev_heading = block
                break

    # 章节上下文（当前块前后各 window_size 个块）
    section_start = max(0, current_index - window_size)
    section_end = min(len(blocks), current_index + window_size + 1)
    section_context = [
        blocks[i]
        for i in range(section_start, section_end)
        if i != current_index and blocks[i].get("text", "").strip()
    ]

    return BlockContext(
        block_id=current_block.get("id", ""),
        text=current_block.get("text", ""),
        block_type=current_block.get("type"),
        page_index=current_block.get("page_index", 0),
        block_index=current_index,
        prev_block=prev_block,
        next_block=next_block,
        prev_heading=prev_heading,
        section_context=section_context,
    )


def build_context_prompt(context: BlockContext, lang_out: str) -> str:
    """
    构建包含上下文的翻译提示

    Args:
        context: 块上下文
        lang_out: 目标语言

    Returns:
        构建的提示文本
    """
    parts = []
    
    # 如果有前一个标题，添加到上下文
    if context.prev_heading and context.prev_heading.get("text"):
        parts.append(f"Section/Chapter: {context.prev_heading.get('text')}")
    
    # 如果有前一个块，添加到上下文（用于理解衔接）
    if context.prev_block and context.prev_block.get("text"):
        prev_text = context.prev_block.get("text", "").strip()
        if prev_text and len(prev_text) < 200:  # 只包含较短的上下文
            parts.append(f"Previous context: {prev_text}")
    
    # 当前要翻译的文本
    parts.append(f"Text to translate: {context.text}")
    
    # 如果有下一个块的开头，添加到上下文（帮助理解句子结尾）
    if context.next_block and context.next_block.get("text"):
        next_text = context.next_block.get("text", "").strip()
        if next_text:
            # 只取下一个块的开头（最多50字符）
            next_snippet = next_text[:50] + ("..." if len(next_text) > 50 else "")
            parts.append(f"Following context (beginning): {next_snippet}")
    
    prompt = "\n\n".join(parts)
    return prompt


async def translate_with_context(
    provider: BaseProvider,
    context: BlockContext,
    meta: TranslateMeta,
    *,
    use_context: bool = True,
) -> str:
    """
    使用上下文进行翻译

    Args:
        provider: 翻译服务提供者
        context: 块上下文
        meta: 翻译元数据
        use_context: 是否使用上下文

    Returns:
        翻译结果
    """
    if not use_context or not context.prev_block and not context.next_block and not context.prev_heading:
        # 没有上下文，直接翻译
        return await provider.translate(context.text, meta)
    
    # 构建包含上下文的提示
    context_prompt = build_context_prompt(context, meta.lang_out)
    
    # 创建新的元数据（标记使用了上下文）
    enhanced_meta = TranslateMeta(
        lang_in=meta.lang_in,
        lang_out=meta.lang_out,
        document_id=meta.document_id,
        block_type=meta.block_type,
        glossary=meta.glossary,
    )
    
    # 翻译（注意：这里的 context_prompt 包含了上下文，但实际翻译时可能需要特殊处理）
    # 对于 Ollama 等模型，可以直接将上下文放入 prompt
    
    # 对于某些提供者，可能需要特殊处理上下文
    # 这里先尝试直接翻译（如果提供者支持的话）
    try:
        # 如果提供者有 _translate_with_context 方法，使用它
        if hasattr(provider, "_translate_with_context"):
            return await provider._translate_with_context(context_prompt, enhanced_meta)
        else:
            # 否则，将上下文合并到文本中
            # 注意：需要确保模型能理解这种格式
            full_text = f"{context_prompt}\n\nTranslation:"
            translated = await provider.translate(full_text, enhanced_meta)
            
            # 提取翻译结果（可能包含一些额外的说明文字）
            # 简单策略：如果结果以 "Text to translate:" 开头，提取后面的部分
            if "Text to translate:" in translated:
                lines = translated.split("\n\n")
                for i, line in enumerate(lines):
                    if line.startswith("Text to translate:"):
                        # 取下一个非空行作为翻译结果
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip():
                                return lines[j].strip()
                # 如果找不到，返回整个翻译结果
                return translated.strip()
            
            return translated.strip()
    except Exception as e:
        logger.warning(f"上下文感知翻译失败，回退到普通翻译: {e}")
        # 回退到普通翻译
        return await provider.translate(context.text, meta)


def group_consecutive_blocks(
    blocks: list[dict[str, Any]],
    max_group_size: int = 3,
    max_group_length: int = 1000,
) -> list[list[int]]:
    """
    将连续的相似块分组，以便联合翻译

    Args:
        blocks: 文本块列表
        max_group_size: 最大组大小（块数量）
        max_group_length: 最大组长度（字符数）

    Returns:
        分组索引列表，每个组是一个索引列表
    """
    groups: list[list[int]] = []
    current_group: list[int] = []
    current_length = 0

    for i, block in enumerate(blocks):
        text = block.get("text", "").strip()
        if not text:
            continue
        
        block_type = block.get("type", "paragraph")
        
        # 标题和特殊块不与其他块合并
        if block_type in ("heading", "title", "caption", "formula"):
            # 先保存当前组
            if current_group:
                groups.append(current_group)
                current_group = []
                current_length = 0
            # 标题单独成组（可选）
            continue
        
        # 检查是否可以添加到当前组
        text_length = len(text)
        can_add = (
            len(current_group) < max_group_size
            and current_length + text_length <= max_group_length
        )

        if can_add and current_group:
            # 添加到当前组
            current_group.append(i)
            current_length += text_length
        else:
            # 开始新组
            if current_group:
                groups.append(current_group)
            current_group = [i]
            current_length = text_length

    # 添加最后一组
    if current_group:
        groups.append(current_group)

    return groups

