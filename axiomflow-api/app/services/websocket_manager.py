"""
WebSocket 连接管理器

用于管理文档进度更新的 WebSocket 连接，支持多客户端订阅。
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """管理 WebSocket 连接，支持按 document_id 订阅进度更新"""

    def __init__(self):
        # document_id -> Set[WebSocket]
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, document_id: str) -> None:
        """连接 WebSocket 并订阅文档进度更新"""
        await websocket.accept()
        
        async with self._lock:
            if document_id not in self._connections:
                self._connections[document_id] = set()
            self._connections[document_id].add(websocket)
        
        logger.info(f"WebSocket 连接: document_id={document_id}, 当前连接数={len(self._connections.get(document_id, set()))}")

    async def disconnect(self, websocket: WebSocket, document_id: str) -> None:
        """断开 WebSocket 连接"""
        async with self._lock:
            if document_id in self._connections:
                self._connections[document_id].discard(websocket)
                if not self._connections[document_id]:
                    del self._connections[document_id]
        
        logger.info(f"WebSocket 断开: document_id={document_id}")

    async def broadcast_progress(self, document_id: str, progress_data: dict) -> None:
        """向所有订阅该文档的客户端广播进度更新"""
        async with self._lock:
            connections = self._connections.get(document_id, set()).copy()
        
        if not connections:
            return
        
        message = json.dumps(progress_data)
        disconnected = set()
        
        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"发送 WebSocket 消息失败: {e}")
                disconnected.add(websocket)
        
        # 清理断开的连接
        if disconnected:
            async with self._lock:
                if document_id in self._connections:
                    self._connections[document_id] -= disconnected
                    if not self._connections[document_id]:
                        del self._connections[document_id]

    def get_connection_count(self, document_id: str) -> int:
        """获取指定文档的连接数"""
        return len(self._connections.get(document_id, set()))


# 全局 WebSocket 管理器实例
websocket_manager = WebSocketManager()

