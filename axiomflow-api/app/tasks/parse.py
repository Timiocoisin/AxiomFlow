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
        def progress_callback(page_done: int, page_total: int, extra: dict | None = None) -> None:
            """解析进度回调（支持更细粒度的 substage / 页内进度）"""
            extra = extra or {}
            substage = str(extra.get("substage") or "extract")
            # 页内细分进度：0~1
            step_done = extra.get("step_done")
            step_total = extra.get("step_total")
            step_ratio = 0.0
            if isinstance(step_done, (int, float)) and isinstance(step_total, (int, float)) and step_total > 0:
                step_ratio = max(0.0, min(1.0, float(step_done) / float(step_total)))

            # 计算更真实的 overall progress：页进度 + 页内进度
            if page_total > 0:
                base_pages_done = max(0.0, float(page_done) - 1.0)  # 当前页尚未完成时，page_done 会是当前页序号
                overall = (base_pages_done + step_ratio) / float(page_total)
            else:
                overall = 0.0

            overall = max(0.0, min(0.999, overall))

            elapsed = time.time() - parse_start
            eta_s = None
            if overall > 0:
                avg = elapsed / overall
                eta_s = max(0.0, (1.0 - overall) * avg)

            # 人类可读 message
            msg = extra.get("message")
            if not isinstance(msg, str) or not msg.strip():
                if isinstance(step_total, (int, float)) and step_total:
                    msg = f"{substage}: {int(step_done or 0)}/{int(step_total)}"
                else:
                    msg = f"{substage}: {page_done}/{page_total} 页"

            # 更新 Job（WS 会读取）
            repo.update_job(
                parse_job_id,
                progress=overall,
                message=msg,
                done=int(extra.get("done") or page_done),
                total=int(extra.get("total") or page_total) if page_total else None,
                eta_s=eta_s,
                substage=substage,
                stage=JobStage.parsing.value,
            )

            # 更新 Celery 任务状态（可选：调试/监控）
            self.update_state(
                state="PROGRESS",
                meta={
                    "stage": "parsing",
                    "substage": substage,
                    "progress": overall,
                    "done": int(extra.get("done") or page_done),
                    "total": int(extra.get("total") or page_total) if page_total else None,
                    "eta_s": eta_s,
                    "message": msg,
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

        # 更新Job为完成状态（解析阶段完成）
        num_pages = doc_dict["num_pages"]
        repo.update_job(
            parse_job_id,
            stage=JobStage.parsing.value,
            progress=1.0,
            message=f"解析完成: {num_pages} 页，开始翻译...",
            done=num_pages,
            total=num_pages,
            eta_s=0.0,
            substage="done",
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

        logger.info(f"PDF解析完成: {document_id}, {num_pages} 页，开始自动翻译...")

        # ========== 自动翻译阶段 ==========
        # 在解析完成后自动进行翻译（使用 Google 翻译）
        try:
            import asyncio
            from ..services.orchestrator import TranslateOrchestrator, TranslateStrategy
            from ..services.providers.base import TranslateMeta

            # 更新Job状态为翻译中
            repo.update_job(
                parse_job_id,
                stage=JobStage.translating.value,
                message="翻译中...",
                done=0,
                total=None,
                eta_s=None,
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
            if total_blocks > 0:
                # 加载术语表
                glossary = {}
                try:
                    if project_id:
                        glossary = repo.get_glossary(project_id)
                except Exception as exc:
                    logger.warning(f"加载术语表失败: {exc}")

                # 创建翻译编排器
                max_concurrent = int(getattr(settings, "translation_max_concurrent", 5))
                orch = TranslateOrchestrator(max_concurrent=max_concurrent)
                strategy = TranslateStrategy(
                    provider="google",  # 使用 Google 翻译
                    use_context=True,
                    context_window_size=2,
                    use_term_consistency=True,
                    use_smart_batching=True,
                )

                # 进度回调
                translate_start = time.time()
                def progress_callback(done: int, total: int) -> None:
                    progress = done / total if total > 0 else 0.0
                    elapsed = time.time() - translate_start
                    eta_s = None
                    if done > 0:
                        avg = elapsed / done
                        eta_s = max(0.0, (total - done) * avg)
                    repo.update_job(
                        parse_job_id,
                        progress=progress,
                        message=f"翻译中: {done}/{total}",
                        done=done,
                        total=total,
                        eta_s=eta_s,
                    )

                # 批量并发翻译
                done = 0
                async def translate_all():
                    nonlocal done
                    for page in structured.get("pages", []):
                        page_blocks = [b for b in page.get("blocks", []) if b in all_blocks]
                        if not page_blocks:
                            continue

                        for block in page_blocks:
                            try:
                                meta = TranslateMeta(
                                    lang_in=lang_in,
                                    lang_out=lang_out,
                                    document_id=document_id,
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
                                    f"翻译块失败 (文档 {document_id}, 块 {block.get('id')}): "
                                    f"{type(exc).__name__}: {str(exc)[:200]}",
                                    exc_info=True,
                                )
                                block["translation"] = f"[翻译失败: {str(exc)[:100]}]"
                                block["translation_error"] = str(exc)
                                block["translation_failed"] = True
                                done += 1
                                if total_blocks:
                                    progress_callback(done, total_blocks)

                # 运行异步翻译
                asyncio.run(translate_all())

                # 保存翻译结果
                repo.update_job(parse_job_id, stage=JobStage.composing.value, message="写入译文中...")
                repo.save_document_json(document_id, structured)

                # 自动导出译文PDF（单语版本）
                try:
                    from ..services.pdf_export import build_translated_pdf
                    
                    pdf_bytes = build_translated_pdf(
                        structured,
                        bilingual=False,  # 单语版本，只显示译文
                        subset_fonts=True,
                        convert_to_pdfa=False,
                    )
                    
                    # 保存译文PDF到存储
                    exports_dir = repo.paths.exports
                    exports_dir.mkdir(parents=True, exist_ok=True)
                    translated_pdf_path = exports_dir / f"{document_id}_translated.pdf"
                    translated_pdf_path.write_bytes(pdf_bytes)
                    
                    # 在文档JSON中记录译文PDF路径（使用绝对路径的字符串形式）
                    # 注意：使用 str() 而不是 as_posix()，确保路径格式正确
                    structured.setdefault("document", {})["translated_pdf_path"] = str(translated_pdf_path)
                    repo.save_document_json(document_id, structured)
                    
                    logger.info(f"译文PDF已导出: {translated_pdf_path}")
                    logger.info(f"译文PDF路径已保存到文档JSON: {structured.get('document', {}).get('translated_pdf_path')}")
                except Exception as e:
                    logger.error(f"导出译文PDF失败: {e}", exc_info=True)
                    # 导出失败不影响整体流程

                # 更新Job为完成状态
                repo.update_job(
                    parse_job_id,
                    stage=JobStage.success.value,
                    progress=1.0,
                    message="解析和翻译完成",
                    done=total_blocks,
                    total=total_blocks,
                    eta_s=0.0,
                )
            else:
                # 没有需要翻译的内容
                repo.update_job(
                    parse_job_id,
                    stage=JobStage.success.value,
                    progress=1.0,
                    message="解析完成（无需要翻译的内容）",
                )

        except Exception as exc:
            logger.error(f"自动翻译失败: {document_id}", exc_info=True)
            # 翻译失败不影响解析结果，只记录错误
            repo.update_job(
                parse_job_id,
                stage=JobStage.parsing.value,  # 回退到parsing状态
                message=f"解析完成，但翻译失败: {str(exc)[:200]}",
            )

        # 最终通知
        try:
            import httpx
            from ..core.config import settings
            
            api_base = getattr(settings, "api_base_url", "http://localhost:8000")
            notify_url = f"{api_base}/v1/ws/documents/{document_id}/notify"
            
            with httpx.Client(timeout=1.0) as client:
                client.post(notify_url)
        except Exception as e:
            logger.debug(f"WebSocket 通知失败（不影响流程）: {e}")

        return {
            "document_id": document_id,
            "num_pages": num_pages,
            "status": "parsed_and_translated",
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

