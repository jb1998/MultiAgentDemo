export type TaskMode = 'auto' | 'single' | 'smart_multi';

export interface TaskStreamEvent {
  type: 'status' | 'step' | 'complete' | 'error';
  status?: string;
  task_id?: number;
  message?: string;
  step?: ExecutionStep;
  task?: Task;
  retry_count?: number;
  error?: string;
}

export interface ExecutionStep {
  id: number;
  step_number: number;
  step_type: string;
  description: string;
  tool_name?: string;
  input_data?: string;
  output_data?: string;
  timestamp: string;
  duration_ms?: number;
}

export interface Task {
  id: number;
  task_text: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: string;
  trace_id?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  execution_steps: ExecutionStep[];
}

export interface Tool {
  name: string;
  description: string;
  keywords: string[];
  version: string;
}

export interface ObservabilityMetrics {
  total_execution_steps: number;
  avg_steps_per_task: number;
  recent_failures: number;
  trace_step_types: Record<string, number>;
}

export interface SecurityMetrics {
  pii_masked_tasks: number;
  injection_blocked_tasks: number;
  validation_rules: string[];
}

export interface Metrics {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  tool_usage: Record<string, number>;
  avg_execution_ms: number;
  success_rate: number;
  tool_success_rate: Record<string, number>;
  observability: ObservabilityMetrics;
  security: SecurityMetrics;
}

export interface AuthUser {
  username: string;
  role: string;
  access_token: string;
}

export interface UserInfo {
  id: number;
  username: string;
  email: string;
  role: string;
  created_at: string;
}

export interface HealthStatus {
  status: string;
  database: string;
  backend: string;
  frontend: string;
  tools_available: number;
  tool_status: Record<string, string>;
  uptime_status: string;
}

export interface AuditLog {
  id: number;
  user_id?: number;
  username?: string;
  action: string;
  message: string;
  level: string;
  metadata_json?: string;
  created_at: string;
}

export interface CostRecord {
  id: number;
  task_id?: number;
  tool_name?: string;
  service_name: string;
  cost_usd: number;
  duration_ms?: number;
  created_at: string;
}

export interface CostSummary {
  total_cost_usd: number;
  tool_costs: Record<string, { total_usd: number; calls: number }>;
  service_costs: Record<string, { total_usd: number; calls: number }>;
  recent_records: CostRecord[];
}
