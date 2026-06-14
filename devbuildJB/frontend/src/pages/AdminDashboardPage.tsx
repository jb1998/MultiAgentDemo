import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import DeleteIcon from '@mui/icons-material/Delete';
import PeopleIcon from '@mui/icons-material/People';
import ListAltIcon from '@mui/icons-material/ListAlt';
import { motion } from 'framer-motion';
import { useCallback, useEffect, useState } from 'react';
import { deleteTask, getAllUsers, getAuditLogs, getTasks } from '../services/taskService';
import type { AuditLog, Task, UserInfo } from '../types/task.types';

export default function AdminDashboardPage() {
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [usersData, tasksData, logsData] = await Promise.all([
        getAllUsers(),
        getTasks(1),
        getAuditLogs(30),
      ]);
      setUsers(usersData);
      setTasks(tasksData.tasks);
      setLogs(logsData);
    } catch {
      setError('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleDelete = async (taskId: number) => {
    if (!window.confirm(`Delete task #${taskId}?`)) return;
    try {
      await deleteTask(taskId);
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
    } catch {
      setError('Failed to delete task');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" className="gradient-text" gutterBottom fontWeight={700}>
        Admin Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Manage users, view all tasks, and delete any task across the system.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Box sx={{ display: 'grid', gap: 3 }}>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <PeopleIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                All Users ({users.length})
              </Typography>
            </Box>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Username</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Created</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell>{u.id}</TableCell>
                    <TableCell>{u.username}</TableCell>
                    <TableCell>{u.email}</TableCell>
                    <TableCell>
                      <Chip
                        label={u.role}
                        size="small"
                        color={u.role === 'admin' ? 'secondary' : 'default'}
                      />
                    </TableCell>
                    <TableCell>{new Date(u.created_at).toLocaleDateString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <AdminPanelSettingsIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                All Tasks ({tasks.length})
              </Typography>
              <Button size="small" onClick={loadData} sx={{ ml: 'auto' }}>
                Refresh
              </Button>
            </Box>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Task</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Result</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tasks.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell>{t.id}</TableCell>
                    <TableCell sx={{ maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {t.task_text}
                    </TableCell>
                    <TableCell>
                      <Chip label={t.status} size="small" color={t.status === 'completed' ? 'success' : t.status === 'failed' ? 'error' : 'default'} />
                    </TableCell>
                    <TableCell sx={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {t.result ?? '—'}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" color="error" onClick={() => handleDelete(t.id)} title="Delete task">
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <ListAltIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                System Logs ({logs.length})
              </Typography>
            </Box>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Message</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>{new Date(log.created_at).toLocaleString()}</TableCell>
                    <TableCell>{log.username ?? '—'}</TableCell>
                    <TableCell><Chip label={log.action} size="small" variant="outlined" /></TableCell>
                    <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {log.message}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </motion.div>
      </Box>
    </Container>
  );
}
