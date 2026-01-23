from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException

from ..schemas.jobs import TranslateJobCreate, TranslateJobCreated
from ..repo import repo
from ..models.domain import Job, JobStage
from ..tasks.translate import run_translate_job
from ..celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/translate", response_model=TranslateJobCreated)
async def create_translate_job(payload: TranslateJobCreate) -> TranslateJobCreated:
    """
    创建翻译任务：使用 Celery 异步执行，立即返回 job_id。
    """
    # 确保文档存在
    try:
        repo.load_document_json(payload.document_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="document_not_found") from exc

    # 创建 Job 记录
    job_id = repo.create_job(payload.document_id, stage=JobStage.pending.value)

    # 提交 Celery 任务
    payload_dict = payload.model_dump()
    task = run_translate_job.delay(job_id, payload_dict)
    repo.update_job(job_id, celery_task_id=task.id, control="running", payload=payload_dict)

    logger.info(f"创建翻译任务 {job_id}，Celery task_id: {task.id}")

    return TranslateJobCreated(job_id=job_id)


@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: str) -> Job:
    """
    查询任务进度。
    """
    try:
        data = repo.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job_not_found") from exc

    created_at = datetime.fromisoformat(data["created_at"])
    updated_at = datetime.fromisoformat(data["updated_at"])

    return Job(
        id=data["id"],
        document_id=data["document_id"],
        stage=JobStage(data["stage"]),
        progress=float(data.get("progress", 0.0)),
        message=data.get("message"),
        done=data.get("done"),
        total=data.get("total"),
        eta_s=data.get("eta_s"),
        control=data.get("control"),
        celery_task_id=data.get("celery_task_id"),
        created_at=created_at,
        updated_at=updated_at,
    )


@router.post("/{job_id}/pause", response_model=Job)
async def pause_job(job_id: str) -> Job:
    try:
        repo.set_job_control(job_id, "paused")
        data = repo.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job_not_found") from exc
    created_at = datetime.fromisoformat(data["created_at"])
    updated_at = datetime.fromisoformat(data["updated_at"])
    return Job(
        id=data["id"],
        document_id=data["document_id"],
        stage=JobStage(data["stage"]),
        progress=float(data.get("progress", 0.0)),
        message=data.get("message"),
        done=data.get("done"),
        total=data.get("total"),
        eta_s=data.get("eta_s"),
        control=data.get("control"),
        celery_task_id=data.get("celery_task_id"),
        created_at=created_at,
        updated_at=updated_at,
    )


@router.post("/{job_id}/resume", response_model=Job)
async def resume_job(job_id: str) -> Job:
    try:
        repo.set_job_control(job_id, "running")
        data = repo.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job_not_found") from exc
    created_at = datetime.fromisoformat(data["created_at"])
    updated_at = datetime.fromisoformat(data["updated_at"])
    return Job(
        id=data["id"],
        document_id=data["document_id"],
        stage=JobStage(data["stage"]),
        progress=float(data.get("progress", 0.0)),
        message=data.get("message"),
        done=data.get("done"),
        total=data.get("total"),
        eta_s=data.get("eta_s"),
        control=data.get("control"),
        celery_task_id=data.get("celery_task_id"),
        created_at=created_at,
        updated_at=updated_at,
    )


@router.post("/{job_id}/cancel", response_model=Job)
async def cancel_job(job_id: str) -> Job:
    try:
        data = repo.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job_not_found") from exc

    task_id = data.get("celery_task_id")
    if task_id:
        try:
            celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")
        except Exception:
            # best-effort
            pass

    repo.set_job_control(job_id, "canceled")
    repo.update_job(job_id, stage=JobStage.canceled.value, message="已取消")
    data = repo.get_job(job_id)
    created_at = datetime.fromisoformat(data["created_at"])
    updated_at = datetime.fromisoformat(data["updated_at"])
    return Job(
        id=data["id"],
        document_id=data["document_id"],
        stage=JobStage(data["stage"]),
        progress=float(data.get("progress", 0.0)),
        message=data.get("message"),
        done=data.get("done"),
        total=data.get("total"),
        eta_s=data.get("eta_s"),
        control=data.get("control"),
        celery_task_id=data.get("celery_task_id"),
        created_at=created_at,
        updated_at=updated_at,
    )


@router.post("/{job_id}/retry", response_model=TranslateJobCreated)
async def retry_job(job_id: str) -> TranslateJobCreated:
    """
    单用户场景：复用同一个 job_id 重新排队执行（重置进度与状态）。
    """
    try:
        data = repo.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job_not_found") from exc

    # 尝试撤销旧任务（如果还在跑）
    old_task_id = data.get("celery_task_id")
    if old_task_id:
        try:
            celery_app.control.revoke(old_task_id, terminate=True, signal="SIGTERM")
        except Exception:
            pass

    payload_dict = data.get("payload")
    if not isinstance(payload_dict, dict):
        raise HTTPException(status_code=400, detail="no_payload_to_retry")

    repo.update_job(
        job_id,
        stage=JobStage.pending.value,
        progress=0.0,
        done=0,
        total=None,
        eta_s=None,
        message="重新排队中...",
        control="running",
    )

    task = run_translate_job.delay(job_id, payload_dict)
    repo.update_job(job_id, celery_task_id=task.id, message="已重新开始")
    return TranslateJobCreated(job_id=job_id)


