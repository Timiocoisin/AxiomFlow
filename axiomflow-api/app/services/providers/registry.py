from __future__ import annotations

from .base import BaseProvider


_PROVIDER_SINGLETONS: dict[str, BaseProvider] = {}


def _get_or_create(name: str, factory: type[BaseProvider]) -> BaseProvider:
    if name not in _PROVIDER_SINGLETONS:
        _PROVIDER_SINGLETONS[name] = factory()
    return _PROVIDER_SINGLETONS[name]


def get_provider(name: str) -> BaseProvider:
    name = (name or "").strip().lower()
    if not name:
        name = "ollama"  # 默认使用 ollama
    if name == "ollama":
        try:
            from .ollama import OllamaProvider
            return _get_or_create("ollama", OllamaProvider)
        except ImportError as e:
            raise ImportError(
                f"Ollama provider requires 'ollama' package. "
                f"Install it with: pip install ollama"
            ) from e
    raise ValueError(f"Unknown provider: {name}")


