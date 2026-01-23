"""
PDF解析任务定义

使用 Celery 执行PDF解析任务，支持实时进度更新。
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Callable, Optional

from celery import Task
from celery.utils.log import get_task_logger

from ..celery_app import celery_app
from ..core.config import settings
from ..core.observability import counter, default_alert_payload, send_alert_webhook
from ..repo import repo
from ..services.pdf_parse import parse_pdf_to_structured_json
from ..models.domain import JobStage

logger = get_task_logger(__name__)

CELERY_PARSE_SUCCESS = counter("axiomflow_celery_parse_success_total", "Celery parse task success total.")
CELERY_PARSE_FAILURE = counter("axiomflow_celery_parse_failure_total", "Celery parse task failure total.")


class ParseCallbackTask(Task):
    """支持进度回调的解析任务基类"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        try:
            CELERY_PARSE_FAILURE.inc()
        except Exception:
            pass
        logger.error(
            f"解析任务 {task_id} 失败: {exc}",
            exc_info=einfo,
            extra={"event": "celery_parse_failure", "task_id": task_id, "exc_type": type(exc).__name__},
        )

        # best-effort alert
        url = str(getattr(settings, "alert_webhook_url", "") or "")
        if url:
            payload = default_alert_payload(
                title="AxiomFlow PDF解析任务失败",
                severity="error",
                task_id=task_id,
                error=f"{type(exc).__name__}: {str(exc)[:400]}",
            )
            send_alert_webhook(url=url, payload=payload)

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功时的回调"""
        try:
            CELERY_PARSE_SUCCESS.inc()
        except Exception:
            pass
        logger.info(
            f"解析任务 {task_id} 成功完成",
            extra={"event": "celery_parse_success", "task_id": task_id},
        )


@celery_app.task(
    bind=True,
    base=ParseCallbackTask,
    name="app.tasks.parse.run_parse_job",
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def run_parse_job(
    self: ParseCallbackTask,
    parse_job_id: str,
    document_id: str,
    pdf_path: str,
    project_id: str,
    lang_in: str,
    lang_out: str,
) -> dict[str, Any]:
    """
    执行PDF解析任务（Celery 任务）

    Args:
        parse_job_id: 解析任务ID（用于跟踪进度）
        document_id: 文档ID
        pdf_path: PDF文件路径
        project_id: 项目ID
        lang_in: 源语言
        lang_out: 目标语言

    Returns:
        解析结果字典
    """
    parse_start = time.time()
    
    # 更新任务状态
    self.update_state(
        state="RUNNING",
        meta={"stage": "parsing", "message": "开始解析PDF...", "done": 0, "total": None},
    )
    
    # 更新Job状态
    repo.update_job(
        parse_job_id,
        stage=JobStage.parsing.value,
        message="解析PDF中...",
        done=0,
        total=None,
        eta_s=None,
        control="running",
    )

    try:
        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        # 创建进度回调函数
        def progress_callback(page_done: int, page_total: int) -> None:
            """解析进度回调"""
            progress = page_done / page_total if page_total > 0 else 0.0
            elapsed = time.time() - parse_start
            eta_s = None
            if page_done > 0:
                avg = elapsed / page_done
                eta_s = max(0.0, (page_total - page_done) * avg)
            
            # 更新Job进度
            repo.update_job(
                parse_job_id,
                progress=progress,
                message=f"解析中: {page_done}/{page_total} 页",
                done=page_done,
                total=page_total,
                eta_s=eta_s,
            )
            
            # 更新Celery任务状态
            self.update_state(
                state="PROGRESS",
                meta={
                    "stage": "parsing",
                    "progress": progress,
                    "done": page_done,
                    "total": page_total,
                    "eta_s": eta_s,
                    "message": f"解析中: {page_done}/{page_total} 页",
                },
            )
            
            # 通过 HTTP 通知 FastAPI 服务器广播 WebSocket 更新
            try:
                import httpx
                from ..core.config import settings
                
                # 获取 API 基础 URL（默认 localhost:8000）
                api_base = getattr(settings, "api_base_url", "http://localhost:8000")
                notify_url = f"{api_base}/v1/ws/documents/{document_id}/notify"
                
                # 发送通知（不等待响应，避免阻塞）
                with httpx.Client(timeout=1.0) as client:
                    client.post(notify_url)
            except Exception as e:
                # WebSocket 通知失败不影响解析任务
                logger.debug(f"WebSocket 通知失败（不影响解析）: {e}")

        # 执行解析（传入进度回调）
        structured = parse_pdf_to_structured_json(
            pdf_path_obj,
            document_id=document_id,
            project_id=project_id,
            lang_in=lang_in,
            lang_out=lang_out,
            progress_callback=progress_callback,  # 传入进度回调
        )

        # 导出高保真 PDF 需要拿到原始 PDF 路径作为底板
        structured.setdefault("document", {})["source_pdf_path"] = pdf_path_obj.as_posix()

        # 确保 num_pages 存在
        doc_dict = structured.setdefault("document", {})
        if "num_pages" not in doc_dict:
            doc_dict["num_pages"] = len(structured.get("pages", []))

        # 保存解析结果
        repo.save_document_json(document_id, structured)

        # 更新Job为完成状态（使用parsing stage表示解析完成，因为success是翻译完成）
        num_pages = doc_dict["num_pages"]
        repo.update_job(
            parse_job_id,
            stage=JobStage.parsing.value,  # 保持parsing状态，但progress=1.0表示完成
            progress=1.0,
            message=f"解析完成: {num_pages} 页",
            done=num_pages,
            total=num_pages,
            eta_s=0.0,
        )
        
        # 通过 HTTP 通知 FastAPI 服务器广播 WebSocket 更新
        try:
            import httpx
            from ..core.config import settings
            
            api_base = getattr(settings, "api_base_url", "http://localhost:8000")
            notify_url = f"{api_base}/v1/ws/documents/{document_id}/notify"
            
            with httpx.Client(timeout=1.0) as client:
                client.post(notify_url)
        except Exception as e:
            logger.debug(f"WebSocket 通知失败（不影响解析）: {e}")

        logger.info(f"PDF解析完成: {document_id}, {num_pages} 页")

        return {
            "document_id": document_id,
            "num_pages": num_pages,
            "status": "parsed",
        }

    except Exception as exc:
        logger.error(f"PDF解析失败: {document_id}", exc_info=True)
        
        # 更新Job为失败状态
        repo.update_job(
            parse_job_id,
            stage=JobStage.failed.value,
            message=f"解析失败: {str(exc)[:200]}",
            control="canceled",
        )
        
        raise

