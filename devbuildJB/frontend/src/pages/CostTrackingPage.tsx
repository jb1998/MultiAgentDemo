import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Container,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import StorageIcon from '@mui/icons-material/Storage';
import BuildIcon from '@mui/icons-material/Build';
import ComputerIcon from '@mui/icons-material/Computer';
import { motion } from 'framer-motion';
import { useCallback, useEffect, useState } from 'react';
import { getCostSummary } from '../services/taskService';
import type { CostSummary } from '../types/task.types';

function formatCost(usd: number): string {
  if (usd < 0.01) return `$${usd.toFixed(6)}`;
  return `$${usd.toFixed(4)}`;
}

export default function CostTrackingPage() {
  const [costs, setCosts] = useState<CostSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadCosts = useCallback(async () => {
    try {
      const data = await getCostSummary();
      setCosts(data);
      setError('');
    } catch {
      setError('Failed to load cost data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCosts();
    const interval = setInterval(loadCosts, 5000);
    return () => clearInterval(interval);
  }, [loadCosts]);

  if (loading && !costs) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  const maxToolCost = Math.max(
    ...Object.values(costs?.tool_costs ?? {}).map((v) => v.total_usd),
    0.0001
  );

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" className="gradient-text" gutterBottom fontWeight={700}>
        Cost Tracking
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
        Local development cost breakdown — database, hosting, and per-tool request costs (auto-refreshes every 5s).
      </Typography>
      <Chip label="Live" size="small" color="success" sx={{ mb: 4 }} />

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <GridCards costs={costs} />

      <Box sx={{ display: 'grid', gap: 3, mt: 3 }}>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <ComputerIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Local Hosting Costs (per request)
              </Typography>
            </Box>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Component</TableCell>
                  <TableCell align="right">Total Spend</TableCell>
                  <TableCell align="right">Invocations</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(costs?.service_costs ?? {}).map(([svc, data]) => (
                  <TableRow key={svc}>
                    <TableCell>{svc}</TableCell>
                    <TableCell align="right">{formatCost(data.total_usd)}</TableCell>
                    <TableCell align="right">{data.calls}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <BuildIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Per-Tool Request Costs
              </Typography>
            </Box>
            {Object.entries(costs?.tool_costs ?? {}).length === 0 ? (
              <Typography color="text.secondary">No tool costs recorded yet. Submit a task to see costs.</Typography>
            ) : (
              Object.entries(costs?.tool_costs ?? {}).map(([tool, data]) => (
                <Box key={tool} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2">{tool}</Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {formatCost(data.total_usd)} ({data.calls} calls)
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={(data.total_usd / maxToolCost) * 100}
                    sx={{ height: 8, borderRadius: 2 }}
                  />
                </Box>
              ))
            )}
          </Paper>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Recent Cost Events
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>Service / Tool</TableCell>
                  <TableCell>Task</TableCell>
                  <TableCell align="right">Cost</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(costs?.recent_records ?? []).map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{new Date(r.created_at).toLocaleTimeString()}</TableCell>
                    <TableCell>{r.tool_name ? `Tool: ${r.tool_name}` : r.service_name}</TableCell>
                    <TableCell>{r.task_id ? `#${r.task_id}` : '—'}</TableCell>
                    <TableCell align="right">{formatCost(r.cost_usd)}</TableCell>
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

function GridCards({ costs }: { costs: CostSummary | null }) {
  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr 1fr' }, gap: 2 }}>
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <AttachMoneyIcon sx={{ fontSize: 32, color: 'success.main', mb: 1 }} />
        <Typography variant="body2" color="text.secondary">Total Spend</Typography>
        <Typography variant="h4" fontWeight={700}>{formatCost(costs?.total_cost_usd ?? 0)}</Typography>
      </Paper>
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <BuildIcon sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
        <Typography variant="body2" color="text.secondary">Tool Requests Billed</Typography>
        <Typography variant="h4" fontWeight={700}>
          {Object.values(costs?.tool_costs ?? {}).reduce((s, v) => s + v.calls, 0)}
        </Typography>
      </Paper>
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <StorageIcon sx={{ fontSize: 32, color: 'info.main', mb: 1 }} />
        <Typography variant="body2" color="text.secondary">Hosting Components</Typography>
        <Typography variant="h4" fontWeight={700}>{Object.keys(costs?.service_costs ?? {}).length}</Typography>
      </Paper>
    </Box>
  );
}
