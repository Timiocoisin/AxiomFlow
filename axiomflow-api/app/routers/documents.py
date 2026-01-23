from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..repo import repo

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}", response_model=dict)
async def get_document(document_id: str) -> dict:
    try:
        return repo.load_document_json(document_id)
    except KeyError as e:
        if "document_not_found" in str(e):
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        raise


@router.get("/{document_id}/source")
async def download_source_pdf(document_id: str):
    """
    下载原始上传的 PDF（给前端 pdf.js 画布渲染用）。
    """
    data = repo.load_document_json(document_id)
    src = (data.get("document") or {}).get("source_pdf_path")
    if not src:
        raise HTTPException(status_code=404, detail="source_pdf_not_found")

    path = Path(str(src))
    # 安全：必须位于 uploads 目录下（避免任意文件读取）
    try:
        uploads_root = repo.paths.uploads.resolve()
        if uploads_root not in path.resolve().parents and path.resolve() != uploads_root:
            raise HTTPException(status_code=400, detail="invalid_source_pdf_path")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid_source_pdf_path") from exc

    if not path.exists():
        raise HTTPException(status_code=404, detail="source_pdf_missing_on_disk")

    filename = path.name
    return FileResponse(path, filename=filename, media_type="application/pdf")


@router.get("/{document_id}/progress", response_model=dict)
async def get_document_progress(document_id: str) -> dict:
    """
    获取文档的实时进度信息（包括上传、解析、翻译等阶段）
    
    返回：
    - status: "uploading" | "parsing" | "parsed" | "translating" | "translated"
    - parse_progress: 0.0-100.0 (解析进度)
    - num_pages: 页面数（解析完成后才有）
    - parse_job: 解析任务信息（包含done/total/eta_s）
    - translate_job: 翻译任务信息（如果有）
    """
    try:
        data = repo.load_document_json(document_id)
        doc_info = data.get("document", {})
        num_pages = doc_info.get("num_pages", 0)
        pages = data.get("pages", [])
        
        # 检查是否有解析完成的标志
        is_parsed = num_pages > 0 or len(pages) > 0
        
        # 如果num_pages为0但pages有数据，更新num_pages
        if num_pages == 0 and len(pages) > 0:
            num_pages = len(pages)
        
        # 查找文档的解析Job（最新的parsing或success状态的job）
        parse_job = None
        try:
            jobs = repo.get_jobs_by_document_id(document_id)
            # 查找解析任务（stage为parsing的job）
            for job in jobs:
                stage = job.get("stage", "")
                # 解析任务通常是parsing阶段
                if stage == "parsing":
                    parse_job = job
                    break
        except Exception as e:
            logger = __import__("logging").getLogger(__name__)
            logger.warning(f"获取jobs失败: {e}")
        
        # 如果已解析完成
        if is_parsed:
            parse_progress = 100.0
            status = "parsed"
        else:
            # 如果文档存在但没有页面数据，尝试从Job获取真实进度
            if parse_job:
                parse_progress = float(parse_job.get("progress", 0.0)) * 100.0
                status = "parsing"
            else:
                # 没有Job信息，返回中间值
                parse_progress = 50.0
                status = "parsing"
        
        # 查找文档的翻译Job（stage为translating或success的job，但不是解析job）
        translate_job = None
        try:
            jobs = repo.get_jobs_by_document_id(document_id)
            for job in jobs:
                stage = job.get("stage", "")
                job_id = job.get("id")
                # 翻译任务（不是解析任务）
                if stage in ("translating", "success") and job_id != parse_job.get("id") if parse_job else True:
                    translate_job = job
                    break
        except Exception:
            pass
        
        return {
            "document_id": document_id,
            "status": status,
            "num_pages": num_pages,
            "parse_progress": parse_progress,
            "parse_job": parse_job,
            "translate_job": translate_job,
        }
    except (KeyError, FileNotFoundError, PermissionError) as e:
        # 文档JSON不存在或无法读取（可能还在上传/解析中）
        logger = __import__("logging").getLogger(__name__)
        logger.debug(f"文档JSON不存在或无法读取: {e}")
        
        # 如果是因为 document_not_found，先查找 Job
        if isinstance(e, KeyError) and "document_not_found" not in str(e):
            raise
        
        # 查找解析Job
        parse_job = None
        try:
            jobs = repo.get_jobs_by_document_id(document_id)
            for job in jobs:
                stage = job.get("stage", "")
                if stage == "parsing":
                    parse_job = job
                    break
        except Exception:
            pass
        
        if parse_job:
            # 有解析Job，说明在上传或解析中
            parse_progress = float(parse_job.get("progress", 0.0)) * 100.0
            status = "parsing" if parse_progress < 100 else "parsed"
        else:
            # 没有Job，可能还在上传
            parse_progress = 0.0
            status = "uploading"
        
        return {
            "document_id": document_id,
            "status": status,
            "num_pages": 0,
            "parse_progress": parse_progress,
            "parse_job": parse_job,
            "translate_job": None,
        }


@router.patch("/{document_id}/blocks/{block_id}", response_model=dict)
async def edit_block_translation(document_id: str, block_id: str, payload: dict) -> dict:
    translated_text = (payload.get("translation") or "").strip()
    apply_all = bool(payload.get("apply_all_same_source", False))

    if apply_all:
        data = repo.load_document_json(document_id)
        target_src = None
        for page in data.get("pages", []):
            for block in page.get("blocks", []):
                if block.get("id") == block_id:
                    target_src = (block.get("text") or "").strip()
                    break
            if target_src:
                break
        if target_src:
            for page in data.get("pages", []):
                for block in page.get("blocks", []):
                    if (block.get("text") or "").strip() == target_src:
                        block["translation"] = translated_text
                        block["edited"] = True
                        block["edited_at"] = __import__("datetime").datetime.utcnow().isoformat()
            repo.save_document_json(document_id, data)
        else:
            repo.update_block_translation(document_id, block_id, translated_text)
    else:
        repo.update_block_translation(document_id, block_id, translated_text)
    return {"ok": True}


