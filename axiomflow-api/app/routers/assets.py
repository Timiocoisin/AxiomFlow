from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..repo import repo
from ..services.assets_extract import extract_assets_from_structured

router = APIRouter(prefix="/documents", tags=["assets"])


@router.post("/{document_id}/assets/extract", response_model=dict)
async def extract_document_assets(document_id: str) -> dict:
    """
    触发一次裁剪：从 regions 中提取 figure/table PNG。
    """
    structured = repo.load_document_json(document_id)
    out_dir = repo.paths.assets / document_id
    assets = extract_assets_from_structured(structured, out_dir=out_dir)
    return {
        "document_id": document_id,
        "assets": [
            {
                "kind": a.kind,
                "page_index": a.page_index,
                "bbox": {"x0": a.x0, "y0": a.y0, "x1": a.x1, "y1": a.y1},
                "download_url": f"/v1/assets/{document_id}/{a.rel_path}",
            }
            for a in assets
        ],
    }


@router.get("/{document_id}/assets", response_model=dict)
async def list_document_assets(document_id: str) -> dict:
    """
    列出已生成的 assets。
    """
    doc_dir = repo.paths.assets / document_id
    if not doc_dir.exists():
        return {"document_id": document_id, "assets": []}

    assets = []
    for p in sorted(doc_dir.glob("*.png")):
        name = p.name
        kind = "figure" if name.startswith("figure_") else ("table" if name.startswith("table_") else "unknown")
        assets.append({"kind": kind, "download_url": f"/v1/assets/{document_id}/{name}", "filename": name})
    return {"document_id": document_id, "assets": assets}


@router.get("/../assets/{document_id}/{filename}")
async def _bad_path():
    # 仅为避免误用；真实路由在下方 /v1/assets
    raise HTTPException(status_code=404, detail="not_found")


assets_router = APIRouter(prefix="/assets", tags=["assets"])


@assets_router.get("/{document_id}/{filename}")
async def download_asset(document_id: str, filename: str):
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="invalid_filename")
    path = repo.paths.assets / document_id / filename
    if not Path(path).exists():
        raise HTTPException(status_code=404, detail="not_found")
    return FileResponse(path, filename=filename, media_type="image/png")


