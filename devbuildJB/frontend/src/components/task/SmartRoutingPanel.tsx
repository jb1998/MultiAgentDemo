import { Box, Chip, Paper, Typography } from '@mui/material';
import RouteIcon from '@mui/icons-material/AltRoute';
import type { ExecutionStep } from '../../types/task.types';
import { buildRoutingPreview } from '../../utils/smartRouting';

interface Props {
  text?: string;
  steps?: ExecutionStep[];
}

function planFromSteps(steps: ExecutionStep[]) {
  const workflow = steps.find((s) => s.step_type === 'workflow' && s.output_data);
  if (!workflow?.output_data) return null;
  try {
    const data = JSON.parse(workflow.output_data);
    if (data.routing_plan) return data.routing_plan as Array<{
      index: number;
      task_text: string;
      tool: string;
      intent: string;
      confidence: number;
    }>;
  } catch {
    return null;
  }
  return null;
}

export default function SmartRoutingPanel({ text, steps }: Props) {
  const executedPlan = steps ? planFromSteps(steps) : null;
  const preview = text ? buildRoutingPreview(text) : [];

  const lines = executedPlan
    ? executedPlan.map((r) => ({
        index: r.index,
        text: r.task_text,
        tool: r.tool,
        intent: r.intent,
        confidence: r.confidence,
      }))
    : preview.map((p) => ({
        index: p.index,
        text: p.text,
        tool: p.suggestedTool,
        intent: p.intent,
        confidence: undefined as number | undefined,
      }));

  if (!lines.length) return null;

  const isPreview = !executedPlan;

  return (
    <Paper sx={{ p: 2, mb: 2, bgcolor: '#FAFAFA', border: '1px solid #E5E5E5' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
        <RouteIcon color="primary" fontSize="small" />
        <Typography variant="subtitle1" fontWeight={600}>
          {isPreview ? 'Smart Routing Preview' : 'Smart Routing Plan'}
        </Typography>
        <Chip size="small" label={`${lines.length} tools`} color="primary" variant="outlined" />
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {lines.map((line) => (
          <Box
            key={line.index}
            sx={{
              p: 1.5,
              borderRadius: 2,
              bgcolor: '#FFFFFF',
              border: '1px solid #E5E5E5',
            }}
          >
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 0.5 }}>
              <Chip size="small" label={`Task ${line.index}`} />
              <Chip size="small" label={line.tool} color="primary" />
              <Chip size="small" label={line.intent} variant="outlined" />
              {line.confidence != null && (
                <Chip size="small" label={`${Math.round(line.confidence * 100)}%`} color="success" variant="outlined" />
              )}
            </Box>
            <Typography variant="body2" color="text.secondary" className="mono">
              {line.text}
            </Typography>
          </Box>
        ))}
      </Box>
    </Paper>
  );
}
