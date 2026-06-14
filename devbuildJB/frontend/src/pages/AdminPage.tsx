import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Container,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import ErrorIcon from '@mui/icons-material/Error';
import ListAltIcon from '@mui/icons-material/ListAlt';
import SecurityIcon from '@mui/icons-material/Security';
import SpeedIcon from '@mui/icons-material/Speed';
import TimelineIcon from '@mui/icons-material/Timeline';
import { motion } from 'framer-motion';
import { useCallback, useEffect, useState } from 'react';
import { getAuditLogs, getMetrics, healthCheck } from '../services/taskService';
import { useAuthStore } from '../store/authStore';
import type { AuditLog, HealthStatus, Metrics } from '../types/task.types';

function MetricCard({
  title,
  value,
  icon,
  color,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <motion.div whileHover={{ scale: 1.02 }}>
      <Paper sx={{ p: 3, height: '100%' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: `${color}22`, color }}>{icon}</Box>
          <Box>
            <Typography variant="body2" color="text.secondary">{title}</Typography>
            <Typography variant="h4" fontWeight={700}>{value}</Typography>
          </Box>
        </Box>
      </Paper>
    </motion.div>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Paper sx={{ p: 3, height: '100%' }}>
      <Typography variant="h6" gutterBottom>{title}</Typography>
      {children}
    </Paper>
  );
}

const levelColor = { info: 'info', warning: 'warning', error: 'error' } as const;

export default function AdminPage() {
  const { role } = useAuthStore();
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadAll = useCallback(async () => {
    try {
      const [m, h, l] = await Promise.all([getMetrics(), healthCheck(), getAuditLogs(50)]);
      setMetrics(m);
      setHealth(h);
      setLogs(l);
      setError('');
    } catch {
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (role !== 'admin') {
      setLoading(false);
      return;
    }
    loadAll();
    const interval = setInterval(loadAll, 5000);
    return () => clearInterval(interval);
  }, [role, loadAll]);

  if (role !== 'admin') {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="warning">Admin access required. Sign in as admin to view analytics.</Alert>
      </Container>
    );
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !metrics) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">{error || 'Metrics unavailable'}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Typography variant="h4" className="gradient-text" fontWeight={700}>
          Analytics & Observability
        </Typography>
        <Chip label="Live · 5s refresh" size="small" color="success" />
      </Box>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Runtime metrics, health checks, audit logs, security posture, and validation coverage.
      </Typography>

      {health && (
        <Paper sx={{ p: 3, mb: 4, border: '1px solid #E5E5E5' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <MonitorHeartIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>System Health Checks</Typography>
            <Chip
              label={health.status}
              size="small"
              color={health.status === 'healthy' ? 'success' : 'warning'}
              sx={{ ml: 1 }}
            />
            <Chip label={health.uptime_status} size="small" variant="outlined" sx={{ ml: 'auto' }} />
          </Box>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption" color="text.secondary">Database</Typography>
              <Chip
                label={health.database}
                size="small"
                color={health.database === 'healthy' ? 'success' : 'error'}
                sx={{ mt: 0.5 }}
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption" color="text.secondary">Backend (FastAPI)</Typography>
              <Chip label={health.backend} size="small" color="success" sx={{ mt: 0.5 }} />
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption" color="text.secondary">Frontend (React)</Typography>
              <Chip label={health.frontend} size="small" color="success" sx={{ mt: 0.5 }} />
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption" color="text.secondary">Tools Registered</Typography>
              <Typography fontWeight={600}>{health.tools_available}</Typography>
            </Grid>
          </Grid>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Tool Status
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {Object.entries(health.tool_status ?? {}).map(([tool, status]) => (
              <Chip
                key={tool}
                label={`${tool}: ${status}`}
                size="small"
                color={status === 'healthy' ? 'success' : 'warning'}
                variant="outlined"
              />
            ))}
          </Box>
        </Paper>
      )}

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Total Tasks" value={metrics.total_tasks} icon={<AnalyticsIcon />} color="#C8102E" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Completed" value={metrics.completed_tasks} icon={<CheckCircleIcon />} color="#15803D" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Failed" value={metrics.failed_tasks} icon={<ErrorIcon />} color="#C8102E" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Avg Time" value={`${metrics.avg_execution_ms.toFixed(1)}ms`} icon={<SpeedIcon />} color="#1A1A1A" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Success Rate" value={`${metrics.success_rate.toFixed(1)}%`} icon={<CheckCircleIcon />} color="#15803D" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Trace Steps" value={metrics.observability.total_execution_steps} icon={<TimelineIcon />} color="#525252" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Avg Steps / Task" value={metrics.observability.avg_steps_per_task.toFixed(1)} icon={<TimelineIcon />} color="#525252" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="PII Masked Tasks" value={metrics.security.pii_masked_tasks} icon={<SecurityIcon />} color="#B45309" />
        </Grid>
      </Grid>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          <SectionCard title="Audit Logs">
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <ListAltIcon color="primary" fontSize="small" />
              <Typography variant="body2" color="text.secondary">
                {logs.length} recent events — login, task submit, PII, injection blocks, quota
              </Typography>
            </Box>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Message</TableCell>
                  <TableCell>Level</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5}>
                      <Typography color="text.secondary">No audit logs yet</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>{new Date(log.created_at).toLocaleString()}</TableCell>
                      <TableCell>{log.username ?? '—'}</TableCell>
                      <TableCell>
                        <Chip label={log.action} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell sx={{ maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {log.message}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={log.level}
                          size="small"
                          color={levelColor[log.level as keyof typeof levelColor] ?? 'default'}
                        />
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </SectionCard>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <SectionCard title="Tool Usage">
            {Object.entries(metrics.tool_usage).length === 0 ? (
              <Typography color="text.secondary">No tool usage data yet</Typography>
            ) : (
              Object.entries(metrics.tool_usage).map(([tool, count]) => (
                <Box key={tool} sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: '1px solid #E5E5E5' }}>
                  <Typography>{tool}</Typography>
                  <Typography fontWeight={600}>{count} uses</Typography>
                </Box>
              ))
            )}
          </SectionCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <SectionCard title="Tool Success Rate">
            {Object.entries(metrics.tool_success_rate).length === 0 ? (
              <Typography color="text.secondary">No tool success data yet</Typography>
            ) : (
              Object.entries(metrics.tool_success_rate).map(([tool, rate]) => (
                <Box key={tool} sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: '1px solid #E5E5E5' }}>
                  <Typography>{tool}</Typography>
                  <Typography fontWeight={600}>{rate.toFixed(1)}%</Typography>
                </Box>
              ))
            )}
          </SectionCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <SectionCard title="Observability">
            <Box sx={{ display: 'grid', gap: 1.25 }}>
              <Typography color="text.secondary">
                Recent failures:{' '}
                <Typography component="span" color="text.primary" fontWeight={600}>
                  {metrics.observability.recent_failures}
                </Typography>
              </Typography>
              {Object.entries(metrics.observability.trace_step_types).map(([stepType, count]) => (
                <Box key={stepType} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography>{stepType}</Typography>
                  <Typography fontWeight={600}>{count}</Typography>
                </Box>
              ))}
            </Box>
          </SectionCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <SectionCard title="Security & Validation">
            <Box sx={{ display: 'grid', gap: 1.25 }}>
              <Typography color="text.secondary">
                Injection blocked:{' '}
                <Typography component="span" color="text.primary" fontWeight={600}>
                  {metrics.security.injection_blocked_tasks}
                </Typography>
              </Typography>
              {metrics.security.validation_rules.map((rule) => (
                <Typography key={rule} variant="body2" color="text.secondary">
                  • {rule}
                </Typography>
              ))}
            </Box>
          </SectionCard>
        </Grid>
      </Grid>
    </Container>
  );
}
