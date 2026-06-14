import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  username: string | null;
  role: string | null;
  setAuth: (token: string, username: string, role: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      username: null,
      role: null,
      setAuth: (token, username, role) => set({ token, username, role }),
      logout: () => set({ token: null, username: null, role: null }),
    }),
    { name: 'bmo-auth' }
  )
);

interface TaskState {
  currentTask: import('../types/task.types').Task | null;
  setCurrentTask: (task: import('../types/task.types').Task | null) => void;
}

export const useTaskStore = create<TaskState>((set) => ({
  currentTask: null,
  setCurrentTask: (task) => set({ currentTask: task }),
}));
