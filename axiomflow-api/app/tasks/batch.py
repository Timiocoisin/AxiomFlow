"""
批量翻译任务定义

使用 Celery 执行批量翻译任务。
"""

from __future__ import annotations

import logging
from typing import Any

from celery import Task
from celery.utils.log import get_task_logger

from ..celery_app import celery_app
from ..repo import repo
from ..models.domain import JobStage
from ..schemas.jobs import TranslateJobCreate
from ..tasks.translate import run_translate_job

logger = get_task_logger(__name__)


class CallbackTask(Task):
    """支持进度回调的任务基类"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        logger.error(f"批量任务 {task_id} 失败: {exc}", exc_info=einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功时的回调"""
        logger.info(f"批量任务 {task_id} 成功完成")


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.batch.run_batch_translate",
    max_retries=2,
    default_retry_delay=120,
)
def run_batch_translate(
    self: CallbackTask, batch_id: str, lang_in: str, lang_out: str, provider: str
) -> dict[str, Any]:
    """
    执行批量翻译任务

    Args:
        batch_id: 批次 ID
        lang_in: 源语言
        lang_out: 目标语言
        provider: 翻译服务提供商

    Returns:
        任务结果字典
    """
    try:
        batch = repo.get_batch(batch_id)
        document_ids = batch.get("document_ids", [])
        job_ids: list[str] = []

        self.update_state(
            state="PROGRESS",
            meta={"total": len(document_ids), "done": 0, "message": "开始批量翻译"},
        )

        for idx, doc_id in enumerate(document_ids):
            if not doc_id:
                continue

            try:
                # 为每个文档创建翻译任务
                payload = TranslateJobCreate(
                    document_id=doc_id, lang_in=lang_in, lang_out=lang_out, provider=provider
                )
                job_id = repo.create_job(doc_id, stage=JobStage.pending.value)
                celery_task = run_translate_job.delay(job_id, payload.model_dump())
                job_ids.append(job_id)  # 使用 job_id 而不是 celery_task.id

                # 更新进度
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "total": len(document_ids),
                        "done": idx + 1,
                        "message": f"已提交 {idx + 1}/{len(document_ids)} 个任务",
                    },
                )
            except Exception as exc:
                logger.error(f"批量翻译任务失败 (文档 {doc_id}): {exc}", exc_info=True)
                # 创建失败的 job 记录
                try:
                    jid = repo.create_job(doc_id, stage=JobStage.failed.value)
                    repo.update_job(jid, stage=JobStage.failed.value, message=str(exc))
                    job_ids.append(jid)
                except Exception:
                    pass

        # 更新 batch 的 job_ids
        repo.update_batch(batch_id, job_ids=job_ids)

        logger.info(f"批量翻译任务 {batch_id} 完成，共 {len(job_ids)} 个任务")

        return {"status": "success", "batch_id": batch_id, "job_ids": job_ids}

    except Exception as exc:
        logger.error(f"批量翻译任务 {batch_id} 失败: {exc}", exc_info=True)
        raise

