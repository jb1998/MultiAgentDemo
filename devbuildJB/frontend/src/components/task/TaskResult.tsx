import { Box, Chip, Typography } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import SyncIcon from '@mui/icons-material/Sync';
import { motion } from 'framer-motion';
import type { Task } from '../../types/task.types';

const statusConfig = {
  pending: { color: 'warning' as const, icon: HourglassEmptyIcon, label: 'Pending' },
  processing: { color: 'info' as const, icon: SyncIcon, label: 'Processing' },
  completed: { color: 'success' as const, icon: CheckCircleIcon, label: 'Completed' },
  failed: { color: 'error' as const, icon: ErrorIcon, label: 'Failed' },
};

interface Props {
  task: Task;
}

function displayResult(task: Task): string {
  if (!task.result) return '';
  if (task.status === 'failed') {
    try {
      const parsed = JSON.parse(task.result) as { error?: string };
      if (parsed.error) return parsed.error;
    } catch {
      /* plain-text error */
    }
  }
  return task.result;
}

export default function TaskResult({ task }: Props) {
  const config = statusConfig[task.status];
  const Icon = config.icon;

  return (
    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}>
      <Box
        sx={{
          p: 3,
          borderRadius: 3,
          background: 'linear-gradient(135deg, rgba(200,16,46,0.04) 0%, rgba(26,26,26,0.03) 100%)',
          border: '1px solid #E5E5E5',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <motion.div
            animate={task.status === 'processing' ? { rotate: 360 } : {}}
            transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}
          >
            <Icon color={config.color} />
          </motion.div>
          <Chip label={config.label} color={config.color} size="small" />
          <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
            Task #{task.id}
          </Typography>
        </Box>

        {task.result && (
          <Box
            className="mono"
            sx={{
              p: 2,
              borderRadius: 2,
              bgcolor: '#F5F5F5',
              color: '#1A1A1A',
              fontSize: '0.95rem',
              lineHeight: 1.7,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {displayResult(task)}
          </Box>
        )}
      </Box>
    </motion.div>
  );
}
