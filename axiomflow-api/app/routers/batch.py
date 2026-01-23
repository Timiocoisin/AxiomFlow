from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..models.domain import JobStage
from ..tasks.batch import run_batch_translate

from ..repo import repo
from ..services.pdf_parse import parse_pdf_to_structured_json

router = APIRouter(prefix="/batches", tags=["batch"])


@router.post("/upload", response_model=dict)
async def batch_upload(
    project_name: str = Form("批量项目"),
    lang_in: str = Form("en"),
    lang_out: str = Form("zh"),
    files: list[UploadFile] = File(...),
    auto_translate: bool = Form(True),
    provider: str = Form("ollama"),
) -> dict:
    """
    Web 端无法直接读取本地目录，目录翻译用“多文件上传”替代：
    一次上传多个 PDF，后端逐个解析并创建 batch 记录。
    """
    if not files:
        raise HTTPException(status_code=400, detail="no_files")

    project_id = repo.create_project(project_name)
    document_ids: list[str] = []
    items: list[dict] = []

    for f in files:
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            continue
        content = await f.read()
        document_id, pdf_path = repo.save_upload(f.filename, content)
        structured = parse_pdf_to_structured_json(
            pdf_path,
            document_id=document_id,
            project_id=project_id,
            lang_in=lang_in,
            lang_out=lang_out,
        )
        structured.setdefault("document", {})["source_pdf_path"] = pdf_path.as_posix()
        repo.save_document_json(document_id, structured)
        document_ids.append(document_id)
        items.append(
            {
                "document_id": document_id,
                "title": f.filename,
                "num_pages": structured.get("document", {}).get("num_pages"),
            }
        )

    batch_id = repo.create_batch(project_id=project_id, document_ids=document_ids)

    # 如果启用自动翻译，提交 Celery 任务
    if auto_translate:
        task = run_batch_translate.delay(batch_id, lang_in, lang_out, provider)
        # 可以将 celery_task_id 存储到 batch 记录中（可选）

    return {"batch_id": batch_id, "project_id": project_id, "documents": items}


@router.get("/{batch_id}", response_model=dict)
async def get_batch(batch_id: str) -> dict:
    b = repo.get_batch(batch_id)
    # 从 document_ids 构建 items，并查找对应的 job
    document_ids = b.get("document_ids", [])
    job_ids = b.get("job_ids", [])
    
    # 构建 items 列表（从 InMemoryRepo 的 items 字段或从 MySQL 的 document_ids）
    items = b.get("items", [])
    if not items:
        # 如果没有 items，从 document_ids 构建
        for i, doc_id in enumerate(document_ids):
            job_id = job_ids[i] if i < len(job_ids) else None
            try:
                structured = repo.load_document_json(doc_id)
                doc_info = structured.get("document", {})
                items.append({
                    "document_id": doc_id,
                    "title": doc_info.get("title", ""),
                    "num_pages": doc_info.get("num_pages", 0),
                    "job_id": job_id,
                })
            except KeyError:
                items.append({
                    "document_id": doc_id,
                    "title": "",
                    "num_pages": 0,
                    "job_id": job_id,
                })
    
    # 附带每个文档的 job 状态快照
    enriched = []
    for it in items:
        job_id = it.get("job_id")
        job = None
        if job_id:
            try:
                job = repo.get_job(job_id)
            except KeyError:
                job = None
        enriched.append({**it, "job": job})
    return {**b, "items": enriched}




