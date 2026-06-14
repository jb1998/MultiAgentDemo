import { useAuthStore } from '../store/authStore';
import type { Task, TaskMode, TaskStreamEvent } from '../types/task.types';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

export async function submitTaskStream(
  taskText: string,
  mode: TaskMode,
  onEvent: (event: TaskStreamEvent) => void,
): Promise<Task> {
  const token = useAuthStore.getState().token;
  const response = await fetch(`${API_URL}/tasks/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ task_text: taskText, mode }),
  });

  if (!response.ok) {
    let detail = 'Failed to submit task';
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }

  if (!response.body) {
    throw new Error('Streaming not supported');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalTask: Task | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const payload = JSON.parse(line.slice(6)) as TaskStreamEvent;
      onEvent(payload);
      if (payload.type === 'complete' && payload.task) {
        finalTask = payload.task;
      }
      if (payload.type === 'error') {
        throw new Error(payload.error || 'Stream error');
      }
    }
  }

  if (!finalTask) {
    throw new Error('Stream ended without a result');
  }
  return finalTask;
}
