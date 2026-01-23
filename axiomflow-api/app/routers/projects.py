from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from ..core.ids import new_id
from ..models.domain import Document
from ..repo import repo
from ..services.pdf_parse import parse_pdf_to_structured_json

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=dict)
async def create_project(name: str = Form("我的项目")) -> dict:
    project_id = repo.create_project(name)
    return {"project_id": project_id}


@router.get("/{project_id}/documents", response_model=dict)
async def get_project_documents(project_id: str) -> dict:
    """获取项目下的所有文档列表"""
    # 检查项目是否存在（通过尝试获取文档列表，如果项目不存在会返回空列表）
    if hasattr(repo, "get_documents_by_project_id"):
        documents = repo.get_documents_by_project_id(project_id)
    else:
        # InMemoryRepo 不支持，返回空列表
        documents = []
    
    return {
        "project_id": project_id,
        "documents": documents,
    }


@router.post("/{project_id}/files", response_model=dict)
async def upload_pdf_to_project(
    project_id: str,
    file: UploadFile = File(...),
    lang_in: str = Form("en"),
    lang_out: str = Form("zh"),
) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported")

    content = await file.read()
    document_id, pdf_path = repo.save_upload(file.filename, content)

    # 先在数据库中创建 Document 记录（Job 需要外键引用）
    repo.create_document(
        document_id=document_id,
        project_id=project_id,
        title=file.filename or "",
        lang_in=lang_in,
        lang_out=lang_out,
        source_pdf_path=str(pdf_path),
    )

    # 创建解析任务Job，用于跟踪进度
    from ..models.domain import JobStage
    parse_job_id = repo.create_job(document_id, stage=JobStage.parsing.value)
    
    # 异步执行解析任务
    from ..tasks.parse import run_parse_job
    task = run_parse_job.delay(
        parse_job_id=parse_job_id,
        document_id=document_id,
        pdf_path=str(pdf_path),
        project_id=project_id,
        lang_in=lang_in,
        lang_out=lang_out,
    )
    
    # 更新Job的Celery任务ID
    repo.update_job(parse_job_id, celery_task_id=task.id, control="running")
    
    # 立即返回，不等待解析完成
    return {
        "project_id": project_id,
        "document_id": document_id,
        "parse_job_id": parse_job_id,  # 返回解析任务ID，用于查询进度
        "title": file.filename,
        "num_pages": 0,  # 解析中，页面数未知
    }


