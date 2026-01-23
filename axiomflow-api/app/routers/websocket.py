"""
WebSocket 路由

提供文档进度更新的实时推送功能。
"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException

from ..services.websocket_manager import websocket_manager
from ..repo import repo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/documents/{document_id}/progress")
async def websocket_document_progress(
    websocket: WebSocket,
    document_id: str,
    heartbeat_interval: Optional[int] = Query(30, description="心跳间隔（秒）"),
):
    """
    WebSocket 端点：订阅文档进度更新
    
    客户端连接后，服务器会：
    1. 立即发送当前进度状态
    2. 每当进度更新时，推送新的进度数据
    3. 定期发送心跳保持连接
    
    消息格式：
    ```json
    {
        "type": "progress" | "heartbeat" | "error",
        "document_id": "...",
        "status": "uploading" | "parsing" | "parsed",
        "parse_progress": 0.0-100.0,
        "num_pages": 0,
        "parse_job": {
            "id": "...",
            "stage": "...",
            "progress": 0.0-1.0,
            "done": 0,
            "total": 0,
            "eta_s": 0.0,
            "message": "..."
        }
    }
    ```
    """
    await websocket_manager.connect(websocket, document_id)
    
    try:
        # 立即发送当前进度状态
        try:
            progress_data = await get_document_progress_data(document_id)
            await websocket.send_json({
                "type": "progress",
                **progress_data,
            })
        except Exception as e:
            logger.warning(f"获取初始进度失败: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"获取文档进度失败: {str(e)}",
            })
        
        # 心跳任务
        async def send_heartbeat():
            while True:
                await asyncio.sleep(heartbeat_interval)
                try:
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": asyncio.get_event_loop().time(),
                    })
                except Exception:
                    break  # 连接已断开
        
        heartbeat_task = asyncio.create_task(send_heartbeat())
        
        # 保持连接，等待客户端断开
        try:
            while True:
                # 接收客户端消息（用于保持连接活跃）
                data = await websocket.receive_text()
                # 可以处理客户端发送的消息（如取消订阅等）
                logger.debug(f"收到客户端消息: {data}")
        except WebSocketDisconnect:
            logger.info(f"客户端断开连接: document_id={document_id}")
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
    
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}", exc_info=True)
    finally:
        await websocket_manager.disconnect(websocket, document_id)


async def get_document_progress_data(document_id: str) -> dict:
    """获取文档进度数据（与 REST API 相同的逻辑）"""
    # 先查找解析Job
    parse_job = None
    try:
        jobs = repo.get_jobs_by_document_id(document_id)
        for job in jobs:
            stage = job.get("stage", "")
            if stage == "parsing":
                parse_job = job
                break
    except Exception as e:
        logger.debug(f"获取jobs失败: {e}")
    
    # 尝试加载文档JSON（可能还不存在）
    try:
        data = repo.load_document_json(document_id)
        doc_info = data.get("document", {})
        num_pages = doc_info.get("num_pages", 0)
        pages = data.get("pages", [])
        
        is_parsed = num_pages > 0 or len(pages) > 0
        
        if num_pages == 0 and len(pages) > 0:
            num_pages = len(pages)
        
        if is_parsed:
            parse_progress = 100.0
            status = "parsed"
        else:
            if parse_job:
                parse_progress = float(parse_job.get("progress", 0.0)) * 100.0
                status = "parsing"
            else:
                parse_progress = 50.0
                status = "parsing"
        
        return {
            "document_id": document_id,
            "status": status,
            "num_pages": num_pages,
            "parse_progress": parse_progress,
            "parse_job": parse_job,
        }
    except (KeyError, FileNotFoundError, PermissionError) as e:
        # 文档JSON不存在或无法读取（可能还在上传/解析中）
        logger.debug(f"文档JSON不存在或无法读取: {e}")
        
        if parse_job:
            parse_progress = float(parse_job.get("progress", 0.0)) * 100.0
            status = "parsing" if parse_progress < 100 else "parsed"
        else:
            parse_progress = 0.0
            status = "uploading"
        
        return {
            "document_id": document_id,
            "status": status,
            "num_pages": 0,
            "parse_progress": parse_progress,
            "parse_job": parse_job,
        }


@router.post("/ws/documents/{document_id}/notify")
async def notify_document_progress(document_id: str):
    """
    内部端点：由 Celery 任务调用，触发 WebSocket 广播
    
    这个端点用于跨进程通信（Celery -> FastAPI）
    """
    try:
        progress_data = await get_document_progress_data(document_id)
        await websocket_manager.broadcast_progress(
            document_id,
            {
                "type": "progress",
                **progress_data,
            },
        )
        return {"status": "ok", "connections": websocket_manager.get_connection_count(document_id)}
    except Exception as e:
        logger.error(f"通知进度更新失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

