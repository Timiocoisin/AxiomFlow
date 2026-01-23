"""
翻译任务定义

使用 Celery 执行翻译任务，支持多 worker、任务持久化、自动重试。
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from celery import Task
from celery.utils.log import get_task_logger

from ..celery_app import celery_app
from ..core.config import settings
from ..core.observability import counter, default_alert_payload, send_alert_webhook
from ..repo import repo
from ..services.orchestrator import TranslateOrchestrator, TranslateStrategy
from ..services.providers.base import TranslateMeta
from ..models.domain import JobStage
from ..schemas.jobs import TranslateJobCreate
from ..services.retry_utils import create_error_context

logger = get_task_logger(__name__)

CELERY_TASK_SUCCESS = counter("axiomflow_celery_task_success_total", "Celery task success total.")
CELERY_TASK_FAILURE = counter("axiomflow_celery_task_failure_total", "Celery task failure total.")
CELERY_TASK_RETRY = counter("axiomflow_celery_task_retry_total", "Celery task retry total.")
CELERY_TRANSLATE_BLOCK_FAIL = counter(
    "axiomflow_translate_block_fail_total",
    "Per-block translation failures in Celery job.",
)


class CallbackTask(Task):
    """支持进度回调的任务基类"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        try:
            CELERY_TASK_FAILURE.inc()
        except Exception:
            pass
        logger.error(
            f"任务 {task_id} 失败: {exc}",
            exc_info=einfo,
            extra={"event": "celery_task_failure", "task_id": task_id, "exc_type": type(exc).__name__},
        )

        # best-effort alert
        url = str(getattr(settings, "alert_webhook_url", "") or "")
        if url:
            payload = default_alert_payload(
                title="AxiomFlow Celery task failed",
                severity="error",
                task_id=task_id,
                error=f"{type(exc).__name__}: {str(exc)[:400]}",
            )
            send_alert_webhook(url=url, payload=payload)

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功时的回调"""
        try:
            CELERY_TASK_SUCCESS.inc()
        except Exception:
            pass
        logger.info(
            f"任务 {task_id} 成功完成",
            extra={"event": "celery_task_success", "task_id": task_id},
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """任务重试时的回调"""
        try:
            CELERY_TASK_RETRY.inc()
        except Exception:
            pass
        logger.warning(
            f"任务 {task_id} 重试: {exc}",
            extra={"event": "celery_task_retry", "task_id": task_id, "exc_type": type(exc).__name__},
        )


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.translate.run_translate_job",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # 最大重试延迟 10 分钟
    retry_jitter=True,  # 添加随机抖动
)
def run_translate_job(self: CallbackTask, job_id: str, payload_dict: dict[str, Any]) -> dict[str, Any]:
    """
    执行翻译任务（Celery 任务）

    Args:
        job_id: 任务 ID
        payload_dict: TranslateJobCreate 的字典表示

    Returns:
        任务结果字典
    """
    # 更新 Celery 任务状态
    self.update_state(state="RUNNING", meta={"stage": "translating", "message": "开始翻译..."})

    job_start = time.time()
    try:
        # 从字典重建 payload
        payload = TranslateJobCreate(**payload_dict)

        # 更新 Job 状态
        repo.update_job(job_id, stage=JobStage.parsing.value, message="解析文档中...", done=0, total=None, eta_s=None, control="running")

        # 加载文档
        structured = repo.load_document_json(payload.document_id)

        # 获取并发配置
        max_concurrent = int(getattr(settings, "translation_max_concurrent", 5))
        orch = TranslateOrchestrator(max_concurrent=max_concurrent)
        strategy = TranslateStrategy(
            provider=payload.provider,
            use_context=payload.use_context if payload.use_context is not None else True,
            context_window_size=payload.context_window_size if payload.context_window_size is not None else 2,
            use_term_consistency=payload.use_term_consistency if payload.use_term_consistency is not None else True,
            use_smart_batching=payload.use_smart_batching if payload.use_smart_batching is not None else True,
        )

        # 收集需要翻译的块
        all_blocks: list[dict] = []
        for page_idx, page in enumerate(structured.get("pages", [])):
            for block_idx, block in enumerate(page.get("blocks", [])):
                text = (block.get("text") or "").strip()
                if not text:
                    continue
                if block.get("is_header_footer") or block.get("is_footnote"):
                    continue
                block["_page_idx"] = page_idx
                block["_block_idx"] = block_idx
                all_blocks.append(block)

        total_blocks = len(all_blocks)
        if total_blocks == 0:
            repo.update_job(job_id, stage=JobStage.success.value, message="没有需要翻译的内容")
            return {"status": "success", "message": "没有需要翻译的内容"}

        repo.update_job(job_id, stage=JobStage.translating.value, message="翻译中...", total=total_blocks, done=0)

        logger.info(
            f"开始翻译任务 {job_id}: {total_blocks} 个文本块，并发数: {max_concurrent}",
            extra={
                "event": "translate_job_start",
                "job_id": job_id,
                "document_id": payload.document_id,
                "total_blocks": total_blocks,
                "max_concurrent": max_concurrent,
            },
        )

        # 加载术语表
        glossary = {}
        try:
            project_id = structured.get("document", {}).get("project_id", "")
            if project_id:
                glossary = repo.get_glossary(project_id)
        except Exception as exc:
            logger.warning(f"加载术语表失败: {exc}")

        # 进度回调
        def progress_callback(done: int, total: int) -> None:
            progress = done / total if total > 0 else 0.0
            elapsed = time.time() - job_start
            eta_s = None
            if done > 0:
                avg = elapsed / done
                eta_s = max(0.0, (total - done) * avg)
            repo.update_job(job_id, progress=progress, message=f"翻译中: {done}/{total}", done=done, total=total, eta_s=eta_s)
            # 更新 Celery 任务状态
            self.update_state(
                state="PROGRESS",
                meta={
                    "progress": progress,
                    "done": done,
                    "total": total,
                    "eta_s": eta_s,
                    "message": f"翻译中: {done}/{total}",
                },
            )

        # 批量并发翻译
        done = 0
        failed_blocks: list[dict] = []

        async def translate_all():
            nonlocal done, failed_blocks
            for page in structured.get("pages", []):
                page_blocks = [b for b in page.get("blocks", []) if b in all_blocks]
                if not page_blocks:
                    continue

                for block in page_blocks:
                    # cooperative pause/cancel (single-user UX)
                    while True:
                        j = repo.get_job(job_id)
                        ctl = j.get("control") or "running"
                        if ctl == "paused":
                            repo.update_job(job_id, message="已暂停（可在前端继续）")
                            await asyncio.sleep(0.5)
                            continue
                        if ctl == "canceled":
                            repo.update_job(job_id, stage=JobStage.canceled.value, message="已取消")
                            return
                        break

                    try:
                        meta = TranslateMeta(
                            lang_in=payload.lang_in,
                            lang_out=payload.lang_out,
                            document_id=payload.document_id,
                            block_type=block.get("type"),
                            glossary=glossary or None,
                        )
                        block["translation"] = await orch.translate_text(
                            block.get("text", ""), meta, strategy
                        )
                        done += 1
                        if total_blocks:
                            progress_callback(done, total_blocks)
                    except Exception as exc:
                        logger.error(
                            f"翻译块失败 (任务 {job_id}, 块 {block.get('id')}): "
                            f"{type(exc).__name__}: {str(exc)[:200]}",
                            exc_info=True,
                            extra={
                                "event": "translate_block_failed",
                                "job_id": job_id,
                                "document_id": payload.document_id,
                                "block_id": block.get("id"),
                                "block_type": block.get("type"),
                            },
                        )
                        try:
                            CELERY_TRANSLATE_BLOCK_FAIL.inc()
                        except Exception:
                            pass
                        block["translation"] = f"[翻译失败: {str(exc)[:100]}]"
                        block["translation_error"] = str(exc)
                        block["translation_failed"] = True
                        failed_blocks.append(block)
                        done += 1
                        if total_blocks:
                            progress_callback(done, total_blocks)

        # 运行异步翻译
        asyncio.run(translate_all())

        # 保存结果
        repo.update_job(job_id, stage=JobStage.composing.value, message="写入译文中...")
        repo.save_document_json(payload.document_id, structured)

        # 更新任务状态
        if failed_blocks:
            failed_count = len(failed_blocks)
            message = f"完成（部分失败: {failed_count}/{total_blocks}）"
            repo.update_job(job_id, stage=JobStage.success.value, message=message)
            logger.warning(
                f"翻译任务 {job_id} 完成，但 {failed_count} 个块翻译失败",
                extra={
                    "event": "translate_job_done_partial",
                    "job_id": job_id,
                    "document_id": payload.document_id,
                    "failed_count": failed_count,
                    "total_blocks": total_blocks,
                    "duration_s": round(time.time() - job_start, 3),
                },
            )
            return {"status": "success", "message": message, "failed_count": failed_count}
        else:
            repo.update_job(job_id, stage=JobStage.success.value, message="翻译完成")
            logger.info(
                f"翻译任务 {job_id} 成功完成",
                extra={
                    "event": "translate_job_done",
                    "job_id": job_id,
                    "document_id": payload.document_id,
                    "total_blocks": total_blocks,
                    "duration_s": round(time.time() - job_start, 3),
                },
            )
            return {"status": "success", "message": "翻译完成"}

    except Exception as exc:
        error_context = create_error_context(
            exc, context={"job_id": job_id, "document_id": payload_dict.get("document_id")}
        )
        error_message = f"任务失败: {type(exc).__name__}: {str(exc)[:200]}"
        logger.error(f"翻译任务 {job_id} 失败: {error_context}", exc_info=True)
        repo.update_job(job_id, stage=JobStage.failed.value, message=error_message)

        # 抛出异常以触发 Celery 重试
        raise

