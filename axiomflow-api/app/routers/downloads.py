from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..repo import repo

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.get("/{filename}")
async def download_file(filename: str):
    # 防止路径穿越
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="invalid_filename")
    path = repo.paths.exports / filename
    if not Path(path).exists():
        raise HTTPException(status_code=404, detail="not_found")
    return FileResponse(path, filename=filename, media_type="application/pdf")


