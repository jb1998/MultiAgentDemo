import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Collapse,
  IconButton,
  InputAdornment,
  Pagination,
  Skeleton,
  TextField,
  Typography,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/Search';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { deleteTask, getTaskTrace, getTasks } from '../../services/taskService';
import { useAuthStore } from '../../store/authStore';
import type { Task } from '../../types/task.types';
import ExecutionTrace from '../task/ExecutionTrace';
import TaskResult from '../task/TaskResult';
import ConfidencePanel from '../task/ConfidencePanel';
import DistributedTraceView from '../task/DistributedTraceView';
import WorkflowDiagram from '../task/WorkflowDiagram';

const statusColor = {
  pending: 'warning',
  processing: 'info',
  completed: 'success',
  failed: 'error',
} as const;

export default function TaskHistory() {
  const { role } = useAuthStore();
  const isAdmin = role === 'admin';
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [inspectedId, setInspectedId] = useState<number | null>(null);
  const [inspectedTask, setInspectedTask] = useState<Task | null>(null);
  const [inspecting, setInspecting] = useState(false);

  const loadTasks = () => {
    setLoading(true);
    getTasks(page, search || undefined)
      .then((data) => {
        setTasks(data.tasks);
        setTotal(data.total);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTasks();
  }, [page, search]);

  const handleDelete = async (taskId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(`Delete task #${taskId}?`)) return;
    await deleteTask(taskId);
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
    if (inspectedId === taskId) {
      setInspectedId(null);
      setInspectedTask(null);
    }
  };

  const handleInspect = async (task: Task, e: React.MouseEvent) => {
    e.stopPropagation();
    if (inspectedId === task.id) {
      setInspectedId(null);
      setInspectedTask(null);
      return;
    }
    setInspecting(true);
    setInspectedId(task.id);
    try {
      const full = await getTaskTrace(task.id);
      setInspectedTask(full);
    } catch {
      setInspectedTask(task);
    } finally {
      setInspecting(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" className="gradient-text" gutterBottom fontWeight={700}>
        {isAdmin ? 'All Task History' : 'My Task History'}
      </Typography>
      {isAdmin && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Admin view — use Inspect on any task to view the full execution trace.
        </Typography>
      )}

      <TextField
        fullWidth
        placeholder="Search tasks..."
        value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        sx={{ mb: 3, maxWidth: 400 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon color="action" />
            </InputAdornment>
          ),
        }}
      />

      {loading ? (
        [1, 2, 3].map((i) => <Skeleton key={i} variant="rounded" height={100} sx={{ mb: 2 }} />)
      ) : tasks.length === 0 ? (
        <Typography color="text.secondary">No tasks yet. Submit one from the home page!</Typography>
      ) : (
        tasks.map((task, i) => (
          <motion.div key={task.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}>
            <Card
              sx={{
                mb: 2,
                transition: 'all 0.2s',
                border: inspectedId === task.id ? '1px solid rgba(200, 16, 46, 0.4)' : '1px solid #E5E5E5',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    #{task.id}
                  </Typography>
                  <Chip label={task.status} size="small" color={statusColor[task.status]} />
                  <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                    {new Date(task.created_at).toLocaleString()}
                  </Typography>
                  {isAdmin && (
                    <>
                      <Button
                        size="small"
                        variant={inspectedId === task.id ? 'contained' : 'outlined'}
                        startIcon={<VisibilityIcon />}
                        onClick={(e) => handleInspect(task, e)}
                        disabled={inspecting && inspectedId === task.id}
                      >
                        Inspect
                      </Button>
                      <IconButton size="small" color="error" onClick={(e) => handleDelete(task.id, e)} title="Delete task">
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </>
                  )}
                </Box>
                <Typography variant="body1">{task.task_text}</Typography>
                {task.result && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    → {task.result}
                  </Typography>
                )}

                {isAdmin && (
                  <Collapse in={inspectedId === task.id && !!inspectedTask}>
                    <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #E5E5E5' }}>
                      {inspectedTask && inspectedTask.id === task.id && (
                        <>
                          {/calculate .+ and .+(uppercase|lowercase|reverse)/i.test(task.task_text) && (
                            <WorkflowDiagram steps={inspectedTask.execution_steps} result={inspectedTask.result} />
                          )}
                          <DistributedTraceView steps={inspectedTask.execution_steps} />
                          <ConfidencePanel steps={inspectedTask.execution_steps} />
                          <TaskResult task={inspectedTask} />
                          <ExecutionTrace steps={inspectedTask.execution_steps} />
                        </>
                      )}
                    </Box>
                  </Collapse>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ))
      )}

      {total > 20 && (
        <Pagination count={Math.ceil(total / 20)} page={page} onChange={(_, p) => setPage(p)} sx={{ mt: 3 }} />
      )}
    </Box>
  );
}
