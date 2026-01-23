from __future__ import annotations

import logging
import re
from typing import Any

try:
    import ollama
except ImportError:
    ollama = None  # type: ignore[assignment, unused-ignore]

from ..core.config_manager import config_manager
from .base import BaseProvider, TranslateMeta

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """
    Ollama 翻译 Provider（本地模型服务）

    特点：
    - 完全本地运行，数据不出服务器
    - 支持自定义模型和 prompt
    - 适合隐私敏感场景

    配置项：
    - api_base: Ollama 服务地址（默认: http://127.0.0.1:11434）
    - model: 使用的模型名称（默认: gemma2）
    """

    name = "ollama"

    def __init__(self) -> None:
        super().__init__()
        
        if ollama is None:
            raise ImportError(
                "ollama package not installed. "
                "Please install it with: pip install ollama"
            )

        # 从配置管理器读取配置（环境变量优先）
        config = config_manager.get_provider_config(self.name)
        self.host = config.api_base or "http://127.0.0.1:11434"
        self.model = config.model or "gemma2"
        
        # Ollama 客户端选项
        self.temperature = 0  # 随机采样可能会打断公式标记
        self.num_predict = 2000  # 默认最大 token 数
        
        # 创建 Ollama 客户端
        self.client = ollama.Client(host=self.host)
        
        logger.info(f"OllamaProvider initialized: host={self.host}, model={self.model}")

    def _build_prompt(self, text: str, meta: TranslateMeta) -> list[dict[str, str]]:
        """
        构建翻译 prompt

        Args:
            text: 待翻译文本
            meta: 翻译元数据

        Returns:
            Ollama 消息列表
        """
        prompt_content = (
            "You are a professional, authentic machine translation engine. "
            "Only Output the translated text, do not include any other text.\n\n"
            f"Translate the following markdown source text to {meta.lang_out}. "
            "Keep the formula notation {v*} unchanged. "
            "Output translation directly without any additional text.\n\n"
            f"Source Text: {text}\n\n"
            "Translated Text:"
        )
        
        return [
            {
                "role": "user",
                "content": prompt_content,
            }
        ]

    def _remove_cot_content(self, content: str) -> str:
        """
        移除 Chain of Thought (CoT) 内容

        某些模型可能会在响应中包含推理过程，需要移除这些内容。

        Args:
            content: 原始响应内容

        Returns:
            清理后的内容
        """
        # 移除 <think>...</think> 标签及其内容
        cleaned = re.sub(
            r"^<think>.+?</think>",
            "",
            content,
            count=1,
            flags=re.DOTALL,
        )
        return cleaned.strip()

    async def _translate_impl(self, text: str, meta: TranslateMeta) -> str:
        """
        实现 Ollama 翻译（基础单句/单块翻译，无显式上下文）。
        """
        return await self._chat_with_ollama(self._build_prompt(text, meta), text, meta)

    async def _translate_with_context(self, context_prompt: str, meta: TranslateMeta) -> str:
        """
        带上下文的翻译接口，供上层的 context_aware_translation 调用。

        Args:
            context_prompt: 已经拼装好的上下文提示文本（含前后文、章节等信息）。
            meta: 翻译元数据。

        Returns:
            翻译后的主文本结果。
        """
        # 这里不直接把长上下文塞进单个 user 消息，而是拆成 system + user，
        # 便于模型区分“指令”和“上下文说明/待翻译内容”。
        system_msg = {
            "role": "system",
            "content": (
                "You are a professional, reliable machine translation engine. "
                "You receive rich surrounding context (previous/next sentences, section titles). "
                "Use the context to choose accurate and consistent terminology, "
                "but only output the final translation text for the main segment to be translated. "
                "Do not echo the context itself or add explanations."
            ),
        }
        user_msg = {
            "role": "user",
            "content": (
                f"Source language: {meta.lang_in}\n"
                f"Target language: {meta.lang_out}\n\n"
                "Below is the context and the main text to translate. "
                "Only output the translation of the main text, in the target language:\n\n"
                f"{context_prompt}\n\n"
                "Translation (only the translated main text):"
            ),
        }
        messages = [system_msg, user_msg]
        # 对于长上下文，自动放宽 num_predict
        return await self._chat_with_ollama(messages, context_prompt, meta)

    async def _chat_with_ollama(
        self,
        messages: list[dict[str, str]],
        raw_text_for_log: str,
        meta: TranslateMeta,
    ) -> str:
        """
        封装实际的 Ollama chat 调用逻辑，统一处理长上下文与错误日志。
        """
        # 动态调整 num_predict（根据输入长度估算，保证长上下文也有足够输出空间）
        estimated_tokens = len(raw_text_for_log) * 5
        num_predict = max(self.num_predict, estimated_tokens)

        options: dict[str, Any] = {
            "temperature": self.temperature,
            "num_predict": num_predict,
        }

        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options=options,
            )

            content = response.message.content or ""
            cleaned_content = self._remove_cot_content(content)

            if not cleaned_content:
                logger.warning(
                    "Ollama returned empty content | "
                    f"text preview: {raw_text_for_log[:80]} | "
                    f"lang: {meta.lang_in}->{meta.lang_out}"
                )
                # 回退：返回原文，避免返回空字符串
                return raw_text_for_log

            return cleaned_content.strip()

        except Exception as e:
            logger.error(
                "Ollama translation failed: %s: %s | text length: %d | lang: %s->%s",
                type(e).__name__,
                str(e),
                len(raw_text_for_log),
                meta.lang_in,
                meta.lang_out,
                exc_info=True,
            )
            raise

