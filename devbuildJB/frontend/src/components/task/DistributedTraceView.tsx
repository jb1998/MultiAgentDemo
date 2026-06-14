import { Box, Chip, LinearProgress, Paper, Typography } from '@mui/material';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import type { ExecutionStep } from '../../types/task.types';

interface TraceLayer {
  name: string;
  duration_ms: number;
  percentage: number;
  status: string;
  details: string;
}

interface DistributedTraceData {
  trace_id: string;
  total_ms: number;
  bottleneck: string;
  layers: TraceLayer[];
}

function parseTrace(steps: ExecutionStep[]): DistributedTraceData | null {
  const traceStep = steps.find((s) => s.step_type === 'distributed_trace');
  if (!traceStep?.output_data) return null;
  try {
    return JSON.parse(traceStep.output_data) as DistributedTraceData;
  } catch {
    return null;
  }
}

interface Props {
  steps: ExecutionStep[];
}

export default function DistributedTraceView({ steps }: Props) {
  const trace = parseTrace(steps);
  if (!trace) return null;

  const maxMs = Math.max(...trace.layers.map((l) => l.duration_ms), 1);

  return (
    <Paper sx={{ p: 3, mb: 3, bgcolor: '#FAFAFA', border: '1px solid #E5E5E5' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Typography variant="h6" fontWeight={600}>
          Distributed Tracing
        </Typography>
        <Chip label={trace.trace_id} size="small" variant="outlined" className="mono" />
        <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
          Total: {trace.total_ms}ms
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <WarningAmberIcon sx={{ fontSize: 16, color: 'warning.main' }} />
        <Typography variant="body2" color="warning.main" fontWeight={600}>
          Bottleneck: {trace.bottleneck}
        </Typography>
      </Box>

      <Box sx={{ display: 'grid', gap: 2 }}>
        {trace.layers.map((layer) => {
          const isBottleneck = layer.name === trace.bottleneck;
          return (
            <Box key={layer.name}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="body2" fontWeight={isBottleneck ? 700 : 400}>
                  {layer.name}
                  {isBottleneck && (
                    <Chip label="BOTTLENECK" size="small" color="warning" sx={{ ml: 1, height: 18, fontSize: '0.65rem' }} />
                  )}
                </Typography>
                <Typography variant="body2" className="mono">
                  {layer.duration_ms}ms ({layer.percentage}%)
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={(layer.duration_ms / maxMs) * 100}
                color={isBottleneck ? 'warning' : 'info'}
                sx={{ height: 12, borderRadius: 2, mb: 0.5 }}
              />
              <Typography variant="caption" color="text.secondary">
                {layer.details}
              </Typography>
            </Box>
          );
        })}
      </Box>
    </Paper>
  );
}
