import { api } from './api';
import type { AuditLog, AuthUser, CostSummary, HealthStatus, Metrics, Task, Tool, UserInfo } from '../types/task.types';

export async function login(username: string, password: string): Promise<AuthUser> {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);
  const { data } = await api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return data;
}

export async function register(
  username: string,
  email: string,
  password: string
): Promise<AuthUser> {
  const { data } = await api.post('/auth/register', { username, email, password });
  return data;
}

export async function submitTask(taskText: string): Promise<Task> {
  const { data } = await api.post('/tasks', { task_text: taskText });
  return data;
}

export async function getTasks(page = 1, search?: string): Promise<{ tasks: Task[]; total: number }> {
  const { data } = await api.get('/tasks', { params: { page, page_size: 20, search } });
  return data;
}

export async function getTask(id: number): Promise<Task> {
  const { data } = await api.get(`/tasks/${id}`);
  return data;
}

export async function deleteTask(id: number): Promise<void> {
  await api.delete(`/tasks/${id}`);
}

export async function getTools(): Promise<Tool[]> {
  const { data } = await api.get('/tools');
  return data;
}

export async function getMetrics(): Promise<Metrics> {
  const { data } = await api.get('/admin/metrics');
  return data;
}

export async function getAllUsers(): Promise<UserInfo[]> {
  const { data } = await api.get('/admin/users');
  return data;
}

export async function getAuditLogs(limit = 100): Promise<AuditLog[]> {
  const { data } = await api.get('/admin/logs', { params: { limit } });
  return data;
}

export async function getCostSummary(): Promise<CostSummary> {
  const { data } = await api.get('/admin/costs');
  return data;
}

export async function getTaskTrace(id: number): Promise<Task> {
  const { data } = await api.get(`/tasks/${id}/trace`);
  return data;
}

export async function healthCheck(): Promise<HealthStatus> {
  const { data } = await api.get('/health');
  return data;
}
