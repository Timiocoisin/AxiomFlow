/**
 * WebSocket 客户端工具
 * 
 * 用于连接文档进度更新的 WebSocket 端点，接收实时进度推送。
 */

import { API_BASE } from "./api";

// 将 HTTP URL 转换为 WebSocket URL
const getWebSocketUrl = (): string => {
  // API_BASE 是 "http://localhost:8000/v1"
  // 转换为 WebSocket URL: "ws://localhost:8000/v1"
  return API_BASE.replace("http://", "ws://").replace("https://", "wss://");
};

export interface ProgressMessage {
  type: "progress" | "heartbeat" | "error";
  document_id: string;
  status: "uploading" | "parsing" | "parsed";
  parse_progress: number;
  num_pages: number;
  parse_job?: {
    id: string;
    stage: string;
    progress: number;
    done?: number;
    total?: number;
    eta_s?: number;
    message?: string;
  };
  message?: string;
}

export class DocumentProgressWebSocket {
  private ws: WebSocket | null = null;
  private documentId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 1秒
  private heartbeatInterval: number | null = null;
  private onMessageCallback: ((data: ProgressMessage) => void) | null = null;
  private onErrorCallback: ((error: Event) => void) | null = null;
  private onCloseCallback: (() => void) | null = null;
  private isManuallyClosed = false; // 标记是否手动断开

  constructor(documentId: string) {
    this.documentId = documentId;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      // 如果已经手动断开，不再重连
      if (this.isManuallyClosed) {
        reject(new Error("WebSocket 已手动断开"));
        return;
      }
      
      try {
        const wsBase = getWebSocketUrl();
        // wsBase 已经是 "ws://localhost:8000/v1"，所以只需要添加 "/ws/documents/..."
        const wsUrl = `${wsBase}/ws/documents/${this.documentId}/progress`;
        console.log(`尝试连接 WebSocket: ${wsUrl}`);
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log(`WebSocket 连接成功: ${this.documentId}`);
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const rawData = JSON.parse(event.data);
            
            // 忽略心跳消息
            if (rawData.type === "heartbeat") {
              return;
            }
            
            console.log(`收到 WebSocket 消息 (${this.documentId}):`, rawData);
            
            // 确保消息格式匹配 ProgressMessage 接口
            const data: ProgressMessage = {
              type: rawData.type || "progress",
              document_id: rawData.document_id || this.documentId,
              status: rawData.status || "parsing",
              parse_progress: rawData.parse_progress || 0,
              num_pages: rawData.num_pages || 0,
              parse_job: rawData.parse_job,
              message: rawData.message,
            };
            
            if (this.onMessageCallback) {
              this.onMessageCallback(data);
            }
          } catch (e) {
            console.error("解析 WebSocket 消息失败:", e, event.data);
          }
        };

        this.ws.onerror = (error) => {
          console.error("WebSocket 错误:", error);
          if (this.onErrorCallback) {
            this.onErrorCallback(error);
          }
          reject(error);
        };

        this.ws.onclose = () => {
          console.log(`WebSocket 连接关闭: ${this.documentId}, 手动断开: ${this.isManuallyClosed}`);
          if (this.onCloseCallback) {
            this.onCloseCallback();
          }
          
          // 如果不是手动断开，才自动重连
          if (!this.isManuallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * this.reconnectAttempts;
            console.log(`${delay}ms 后尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => {
              this.connect().catch(console.error);
            }, delay);
          } else if (!this.isManuallyClosed) {
            console.error("WebSocket 重连失败，已达到最大重试次数");
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  onMessage(callback: (data: ProgressMessage) => void): void {
    this.onMessageCallback = callback;
  }

  onError(callback: (error: Event) => void): void {
    this.onErrorCallback = callback;
  }

  onClose(callback: () => void): void {
    this.onCloseCallback = callback;
  }

  disconnect(): void {
    this.isManuallyClosed = true; // 标记为手动断开
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    if (this.heartbeatInterval !== null) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

