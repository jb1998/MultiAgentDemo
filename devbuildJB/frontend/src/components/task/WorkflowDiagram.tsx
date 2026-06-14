import { Box, Paper, Typography } from '@mui/material';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import type { ExecutionStep } from '../../types/task.types';

interface Props {
  steps: ExecutionStep[];
  result?: string;
}

export default function WorkflowDiagram({ steps, result }: Props) {
  const workflowSteps = steps.filter(
    (s) => s.step_type === 'workflow' || (s.step_type === 'execution' && s.tool_name)
  );
  const toolSteps = steps.filter((s) => s.step_type === 'execution' && s.tool_name);

  if (toolSteps.length < 2) return null;

  return (
    <Paper sx={{ p: 3, mb: 3, bgcolor: '#FAFAFA', border: '1px solid #E5E5E5' }}>
      <Typography variant="h6" gutterBottom fontWeight={600}>
        Multi-Tool Workflow
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1, py: 2 }}>
        {toolSteps.map((step, i) => {
          let stepResult = '';
          try {
            if (step.output_data) {
              const parsed = JSON.parse(step.output_data);
              stepResult = parsed.result ?? step.output_data;
            }
          } catch {
            stepResult = step.output_data ?? '';
          }
          return (
            <Box key={step.id} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
              <Paper
                sx={{
                  p: 2,
                  width: '100%',
                  maxWidth: 360,
                  textAlign: 'center',
                  bgcolor: '#FFFFFF',
                  border: '1px solid #E5E5E5',
                }}
              >
                <Typography variant="subtitle2" color="primary.main" fontWeight={700}>
                  {step.tool_name}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {step.description}
                </Typography>
                {stepResult && (
                  <Typography variant="body1" fontWeight={600} sx={{ mt: 1 }}>
                    → {stepResult}
                  </Typography>
                )}
              </Paper>
              {i < toolSteps.length - 1 && (
                <ArrowDownwardIcon sx={{ color: 'primary.main', my: 0.5 }} />
              )}
            </Box>
          );
        })}
      </Box>
      {result && (
        <Typography variant="h6" textAlign="center" sx={{ mt: 2, color: 'success.main' }}>
          Final: {result}
        </Typography>
      )}
      {workflowSteps.length > 0 && (
        <Typography variant="caption" color="text.secondary" display="block" textAlign="center" sx={{ mt: 1 }}>
          {workflowSteps[0].description}
        </Typography>
      )}
    </Paper>
  );
}
