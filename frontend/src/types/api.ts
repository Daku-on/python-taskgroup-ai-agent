/**
 * API関連の型定義
 */

export interface TaskRequest {
  name: string;
  agent_type: 'llm' | 'database' | 'rag';
  data: Record<string, any>;
}

export interface TaskResponse {
  task_id: string;
  name: string;
  status: 'completed' | 'failed';
  result?: string;
  error?: string;
  created_at: string;
  completed_at?: string;
}

export interface ServiceStatus {
  name: string;
  status: string;
  health: boolean;
  metrics: {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    average_response_time: number;
    success_rate: number;
    error_rate: number;
    uptime_seconds: number;
  };
}

export interface WorkflowRequest {
  name: string;
  steps: Array<{
    service: string;
    operation: string;
    data: Record<string, any>;
    depends_on?: string[];
  }>;
}

export interface WorkflowResponse {
  workflow_id: string;
  result: Record<string, any>;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}