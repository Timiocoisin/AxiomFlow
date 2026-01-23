from __future__ import annotations

"""
持久化配置管理（类似开源项目的 ConfigManager）

目标：
- 支持把 provider 密钥/模型、运行参数等写入本地 JSON 配置文件
- 支持环境变量覆盖（方便生产部署/CI）
- 线程安全（RLock），同一进程多线程/多请求安全读写

说明：
- 这是“运行时配置”（runtime config），与 `app/core/config.py` 的 Pydantic Settings（进程启动配置）互补
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any


def _default_config_path() -> Path:
    # Windows: C:\Users\<user>\.config\AxiomFlow\config.json
    # macOS/Linux: ~/.config/AxiomFlow/config.json
    return Path.home() / ".config" / "AxiomFlow" / "config.json"


@dataclass(frozen=True)
class ProviderConfig:
    api_base: str | None = None
    api_key: str | None = None
    model: str | None = None


class ConfigManager:
    _instance: "ConfigManager | None" = None
    _lock = RLock()

    @classmethod
    def get_instance(cls) -> "ConfigManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self, config_path: str | Path | None = None) -> None:
        self._config_path = Path(config_path) if config_path else _default_config_path()
        self._config_data: dict[str, Any] = {}
        self._ensure_exists()

    def _ensure_exists(self) -> None:
        with self._lock:
            if not self._config_path.exists():
                self._config_path.parent.mkdir(parents=True, exist_ok=True)
                self._config_data = {"providers": {}, "app": {}}
                self._save()
            else:
                self._load()

    def _load(self) -> None:
        with self._lock:
            try:
                self._config_data = json.loads(self._config_path.read_text(encoding="utf-8") or "{}")
            except Exception:
                # 配置损坏时，回退到默认
                self._config_data = {"providers": {}, "app": {}}
                self._save()

            if "providers" not in self._config_data:
                self._config_data["providers"] = {}
            if "app" not in self._config_data:
                self._config_data["app"] = {}

    def _save(self) -> None:
        with self._lock:
            self._config_path.write_text(
                json.dumps(self._config_data, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )

    # -------- Generic API --------
    def get(self, key: str, default: Any = None) -> Any:
        """
        读取配置（支持点号路径，如 "app.max_concurrent"）
        环境变量覆盖：会尝试读取同名 ENV（点号替换为下划线并大写）
        """
        env_key = key.replace(".", "_").upper()
        if env_key in os.environ:
            return os.environ[env_key]

        with self._lock:
            cur: Any = self._config_data
            for part in key.split("."):
                if not isinstance(cur, dict) or part not in cur:
                    return default
                cur = cur[part]
            return cur

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            cur: dict[str, Any] = self._config_data
            parts = key.split(".")
            for part in parts[:-1]:
                nxt = cur.get(part)
                if not isinstance(nxt, dict):
                    nxt = {}
                    cur[part] = nxt
                cur = nxt
            cur[parts[-1]] = value
            self._save()

    def delete(self, key: str) -> None:
        with self._lock:
            cur: Any = self._config_data
            parts = key.split(".")
            for part in parts[:-1]:
                if not isinstance(cur, dict) or part not in cur:
                    return
                cur = cur[part]
            if isinstance(cur, dict) and parts[-1] in cur:
                del cur[parts[-1]]
                self._save()

    def as_dict(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._config_data))

    # -------- Provider API --------
    def get_provider_config(self, provider_name: str) -> ProviderConfig:
        """
        读取 provider 配置（环境变量优先）。
        """
        name = (provider_name or "").strip().lower()
        if not name:
            return ProviderConfig()

        # default schema (best-effort)
        api_base = self.get(f"providers.{name}.api_base")
        api_key = self.get(f"providers.{name}.api_key")
        model = self.get(f"providers.{name}.model")
        return ProviderConfig(api_base=api_base, api_key=api_key, model=model)

    # -------- Parser Settings API --------
    def get_parser_config(self) -> dict:
        """获取解析器配置（vfont, vchar 等）"""
        return {
            "vfont": self.get("parser.vfont", ""),
            "vchar": self.get("parser.vchar", ""),
        }

    def set_parser_config(self, vfont: str | None = None, vchar: str | None = None) -> None:
        """设置解析器配置"""
        if vfont is not None:
            self.set("parser.vfont", vfont)
        if vchar is not None:
            self.set("parser.vchar", vchar)

    def set_provider_config(self, provider_name: str, cfg: dict[str, Any]) -> None:
        name = (provider_name or "").strip().lower()
        if not name:
            raise ValueError("provider_name_required")

        allowed = {"api_base", "api_key", "model"}
        clean = {k: v for k, v in cfg.items() if k in allowed}
        self.set(f"providers.{name}", clean)


config_manager = ConfigManager.get_instance()


