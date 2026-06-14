import {
  Timeline,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineItem,
  TimelineSeparator,
} from '@mui/lab';
import { Box, Chip, Collapse, Typography } from '@mui/material';
import BuildIcon from '@mui/icons-material/Build';
import InputIcon from '@mui/icons-material/Input';
import OutputIcon from '@mui/icons-material/Output';
import PsychologyIcon from '@mui/icons-material/Psychology';
import ReplayIcon from '@mui/icons-material/Replay';
import TimelineIcon from '@mui/icons-material/Timeline';
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import type { ExecutionStep } from '../../types/task.types';

const stepIcons: Record<string, typeof InputIcon> = {
  input: InputIcon,
  analyze: PsychologyIcon,
  tool_selection: PsychologyIcon,
  execution: BuildIcon,
  output: OutputIcon,
  workflow: PsychologyIcon,
  distributed_trace: TimelineIcon,
  persist: OutputIcon,
  retry: ReplayIcon,
  error: OutputIcon,
};

const stepColors: Record<string, 'primary' | 'secondary' | 'success' | 'error' | 'grey' | 'warning' | 'info'> = {
  input: 'primary',
  analyze: 'secondary',
  tool_selection: 'secondary',
  execution: 'success',
  output: 'success',
  workflow: 'warning',
  distributed_trace: 'primary',
  persist: 'success',
  retry: 'warning',
  error: 'error',
};

interface Props {
  steps: ExecutionStep[];
  live?: boolean;
}

export default function ExecutionTrace({ steps, live = false }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (!steps.length) return null;

  return (
    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2, mt: 3 }}>
        <Typography variant="h6">Execution Trace</Typography>
        {live && (
          <Chip size="small" label="Live" color="info" className="pulse-glow" />
        )}
      </Box>
      <Timeline position="alternate" sx={{ p: 0, m: 0 }}>
        <AnimatePresence>
          {steps.map((step, i) => {
            const Icon = stepIcons[step.step_type] || BuildIcon;
            const color = stepColors[step.step_type] || 'grey';
            return (
              <motion.div
                key={step.id ?? `live-${step.step_number}`}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.35 }}
              >
                <TimelineItem>
                  <TimelineSeparator>
                    <TimelineDot color={color} variant={step.step_type === 'retry' ? 'filled' : 'outlined'}>
                      <Icon sx={{ fontSize: 16 }} />
                    </TimelineDot>
                    {i < steps.length - 1 && <TimelineConnector sx={{ bgcolor: '#E5E5E5' }} />}
                  </TimelineSeparator>
                  <TimelineContent>
                    <Box
                      onClick={() => setExpanded(expanded === (step.id ?? step.step_number) ? null : (step.id ?? step.step_number))}
                      sx={{
                        p: 2,
                        mb: 2,
                        borderRadius: 2,
                        cursor: 'pointer',
                        bgcolor: step.step_type === 'retry' ? 'rgba(255, 152, 0, 0.06)' : '#FAFAFA',
                        border: step.step_type === 'retry' ? '1px solid rgba(255, 152, 0, 0.35)' : '1px solid #E5E5E5',
                        '&:hover': { bgcolor: '#F5F5F5' },
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <Typography variant="subtitle2">Step {step.step_number}</Typography>
                        <Chip label={step.step_type.replace('_', ' ')} size="small" variant="outlined" />
                        {step.tool_name && <Chip label={step.tool_name} size="small" color="primary" />}
                        {step.duration_ms != null && (
                          <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                            {step.duration_ms}ms
                          </Typography>
                        )}
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {step.description}
                      </Typography>
                      <Collapse in={expanded === (step.id ?? step.step_number)}>
                        {step.output_data && (
                          <Box
                            className="mono"
                            sx={{
                              mt: 1,
                              p: 1,
                              fontSize: '0.75rem',
                              bgcolor: '#F5F5F5',
                              color: '#1A1A1A',
                              borderRadius: 1,
                              overflow: 'auto',
                            }}
                          >
                            {step.output_data}
                          </Box>
                        )}
                      </Collapse>
                    </Box>
                  </TimelineContent>
                </TimelineItem>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </Timeline>
    </motion.div>
  );
}
