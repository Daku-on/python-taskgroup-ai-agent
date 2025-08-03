/**
 * APIクライアント設定
 */

import axios, { type AxiosResponse } from 'axios';
import type { 
  TaskRequest, 
  TaskResponse, 
  ServiceStatus, 
  WorkflowRequest, 
  WorkflowResponse,
  ApiResponse 
} from '../types/api';

// APIベースURL設定
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// axiosインスタンス作成
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// レスポンスインターセプター
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// APIクライアント関数群
export const api = {
  // ヘルスチェック
  async health(): Promise<ApiResponse<{ status: string; registry: boolean }>> {
    try {
      const response = await apiClient.get('/health');
      return { data: response.data, status: response.status };
    } catch (error: any) {
      return { 
        error: error.message || 'Health check failed', 
        status: error.response?.status || 500 
      };
    }
  },

  // サービス一覧取得
  async getServices(): Promise<ApiResponse<ServiceStatus[]>> {
    try {
      const response = await apiClient.get<ServiceStatus[]>('/services');
      return { data: response.data, status: response.status };
    } catch (error: any) {
      return { 
        error: error.message || 'Failed to fetch services', 
        status: error.response?.status || 500 
      };
    }
  },

  // タスク実行
  async executeTask(request: TaskRequest): Promise<ApiResponse<TaskResponse>> {
    try {
      const response = await apiClient.post<TaskResponse>('/tasks/execute', request);
      return { data: response.data, status: response.status };
    } catch (error: any) {
      return { 
        error: error.message || 'Task execution failed', 
        status: error.response?.status || 500 
      };
    }
  },

  // ワークフロー実行
  async executeWorkflow(request: WorkflowRequest): Promise<ApiResponse<WorkflowResponse>> {
    try {
      const response = await apiClient.post<WorkflowResponse>('/workflows/execute', request);
      return { data: response.data, status: response.status };
    } catch (error: any) {
      return { 
        error: error.message || 'Workflow execution failed', 
        status: error.response?.status || 500 
      };
    }
  },
};

// WebSocket接続管理
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private listeners: Array<(data: any) => void> = [];
  private reconnectTimeout: number | null = null;
  private maxReconnectAttempts = 5;
  private reconnectAttempts = 0;

  constructor(private url: string = `ws://localhost:8000/ws`) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.listeners.forEach(listener => listener(data));
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff

    this.reconnectTimeout = window.setTimeout(() => {
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      this.connect().catch(() => {
        // Reconnection failed, will try again
      });
    }, delay);
  }

  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.listeners = [];
  }

  addListener(listener: (data: any) => void): void {
    this.listeners.push(listener);
  }

  removeListener(listener: (data: any) => void): void {
    this.listeners = this.listeners.filter(l => l !== listener);
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export default apiClient;