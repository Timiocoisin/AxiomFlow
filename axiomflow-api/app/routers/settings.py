from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..core.config_manager import config_manager

router = APIRouter(prefix="/settings", tags=["settings"])


class ProviderConfigPayload(BaseModel):
    api_base: str | None = None
    api_key: str | None = None
    model: str | None = None


class AppConfigPayload(BaseModel):
    max_concurrent: int | None = Field(default=None, ge=1, le=50)
    pdf_font: str | None = None  # 字体路径


class ParserConfigPayload(BaseModel):
    vfont: str | None = Field(default=None, description="公式字体正则表达式，例如 'CM.*|Math.*'")
    vchar: str | None = Field(default=None, description="公式字符正则表达式（可选）")


@router.get("", response_model=dict)
async def get_settings() -> dict:
    """
    获取当前持久化配置（不返回敏感信息明文）。
    注意：环境变量覆盖不写回文件，因此这里只展示持久化配置 + “是否配置”状态。
    """
    data = config_manager.as_dict()

    # 避免明文回传 api_key
    providers = data.get("providers", {}) or {}
    safe_providers = {}
    for name, cfg in providers.items():
        cfg = cfg or {}
        api_key = cfg.get("api_key")
        safe_providers[name] = {
            **{k: v for k, v in cfg.items() if k != "api_key"},
            "api_key_configured": bool(api_key),
        }

    app_cfg = data.get("app", {}) or {}
    parser_cfg = config_manager.get_parser_config()
    # 对齐我们目前用到的字段
    result = {
        "providers": safe_providers,
        "app": {
            "max_concurrent": app_cfg.get("max_concurrent"),
            "pdf_font": app_cfg.get("pdf_font"),
        },
        "parser": parser_cfg,
    }
    return result


@router.put("/providers/{provider_name}", response_model=dict)
async def set_provider(provider_name: str, payload: ProviderConfigPayload) -> dict:
    """
    设置 provider 持久化配置（写入本地 config.json）。
    生产环境建议用环境变量注入密钥；此接口主要用于本地/单机部署。
    """
    try:
        config_manager.set_provider_config(provider_name, payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@router.put("/app", response_model=dict)
async def set_app(payload: AppConfigPayload) -> dict:
    """
    设置应用运行参数（持久化）：并发数、导出字体等。
    """
    data = payload.model_dump(exclude_none=True)
    if "max_concurrent" in data:
        config_manager.set("app.max_concurrent", int(data["max_concurrent"]))
    if "pdf_font" in data:
        # 同时兼容老的 AXIOMFLOW_PDF_FONT 读取方式
        config_manager.set("app.pdf_font", data["pdf_font"])
        config_manager.set("AXIOMFLOW_PDF_FONT", data["pdf_font"])
    return {"ok": True}


@router.put("/parser", response_model=dict)
async def set_parser(payload: ParserConfigPayload) -> dict:
    """
    设置解析器配置（持久化）：vfont（公式字体正则）、vchar（公式字符正则）等。
    
    示例 vfont 值：
    - "CM.*|Math.*|MT.*" 匹配 Computer Modern、Math、MathType 字体
    - ".*Ital.*|.*Sym.*" 匹配包含 Ital 或 Sym 的字体名
    """
    data = payload.model_dump(exclude_none=True)
    config_manager.set_parser_config(
        vfont=data.get("vfont"),
        vchar=data.get("vchar"),
    )
    return {"ok": True}


