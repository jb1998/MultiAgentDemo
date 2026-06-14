import { Box, Chip, LinearProgress, Paper, Typography } from '@mui/material';
import type { ExecutionStep } from '../../types/task.types';

interface ToolScore {
  tool: string;
  score: number;
}

interface ConfidenceData {
  confidence: number;
  selected_tool: string;
  all_scores: ToolScore[];
  threshold: number;
  status: string;
}

function parseConfidence(step: ExecutionStep): ConfidenceData | null {
  if (step.step_type !== 'tool_selection' || !step.output_data) return null;
  try {
    const data = JSON.parse(step.output_data);
    if (data.all_scores) return data as ConfidenceData;
    if (data.confidence != null) {
      return {
        confidence: data.confidence,
        selected_tool: data.selected_tool || step.tool_name || '',
        all_scores: data.all_scores || [{ tool: step.tool_name || '', score: data.confidence }],
        threshold: data.threshold ?? 0.15,
        status: data.status || (data.confidence >= 0.8 ? 'HIGH CONFIDENCE' : 'PROCEEDING'),
      };
    }
  } catch {
    return null;
  }
  return null;
}

function confidenceColor(score: number): 'success' | 'warning' | 'error' {
  if (score >= 0.8) return 'success';
  if (score >= 0.15) return 'warning';
  return 'error';
}

interface Props {
  steps: ExecutionStep[];
}

export default function ConfidencePanel({ steps }: Props) {
  const selectionSteps = steps.filter((s) => s.step_type === 'tool_selection');
  const panels = selectionSteps
    .map((step) => ({ step, data: parseConfidence(step) }))
    .filter((p): p is { step: ExecutionStep; data: ConfidenceData } => p.data !== null);

  if (!panels.length) return null;

  return (
    <Box sx={{ mb: 3 }}>
      {panels.map(({ step, data }, idx) => (
        <Paper key={step.id} sx={{ p: 3, mb: 2, bgcolor: '#FAFAFA', border: '1px solid #E5E5E5' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <Typography variant="h6" fontWeight={600}>
              Tool Selection Confidence
            </Typography>
            <Chip label={data.selected_tool} size="small" color="primary" />
            <Chip
              label={data.status}
              size="small"
              color={confidenceColor(data.confidence)}
              sx={{ ml: 'auto' }}
            />
          </Box>

          <Typography variant="body2" color="text.secondary" gutterBottom>
            Selected: <strong>{data.selected_tool}</strong> — {Math.round(data.confidence * 100)}% confidence
          </Typography>
          <LinearProgress
            variant="determinate"
            value={Math.min(data.confidence * 100, 100)}
            color={confidenceColor(data.confidence)}
            sx={{ height: 10, borderRadius: 5, mb: 2 }}
          />

          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            All tools ranked:
          </Typography>
          {data.all_scores.slice(0, 6).map(({ tool, score }) => (
            <Box key={`${idx}-${tool}`} sx={{ mb: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.25 }}>
                <Typography variant="body2">{tool}</Typography>
                <Typography variant="body2" fontWeight={600}>
                  {Math.round(score * 100)}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={Math.min(score * 100, 100)}
                color={tool === data.selected_tool ? 'primary' : 'inherit'}
                sx={{ height: 6, borderRadius: 3, opacity: tool === data.selected_tool ? 1 : 0.5 }}
              />
            </Box>
          ))}
        </Paper>
      ))}
    </Box>
  );
}
