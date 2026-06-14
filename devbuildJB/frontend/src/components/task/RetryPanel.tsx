import { Alert, Box, Chip, Typography } from '@mui/material';
import ReplayIcon from '@mui/icons-material/Replay';
import type { ExecutionStep } from '../../types/task.types';

interface Props {
  steps: ExecutionStep[];
  retryCount?: number;
}

function parseRetryMeta(step: ExecutionStep) {
  if (!step.output_data) return null;
  try {
    const data = JSON.parse(step.output_data);
    return {
      attempt: data.attempt as number | undefined,
      nextAttempt: data.next_attempt as number | undefined,
      maxAttempts: data.max_attempts as number | undefined,
      reason: data.reason as string | undefined,
      backoffMs: data.backoff_ms as number | undefined,
    };
  } catch {
    return null;
  }
}

export default function RetryPanel({ steps, retryCount = 0 }: Props) {
  const retrySteps = steps.filter((s) => s.step_type === 'retry');

  if (retrySteps.length === 0 && retryCount === 0) return null;

  const recovered = steps.some((s) => s.step_type === 'execution' || s.step_type === 'output');
  const lastRetry = retrySteps[retrySteps.length - 1];
  const meta = lastRetry ? parseRetryMeta(lastRetry) : null;

  return (
    <Alert
      severity={recovered ? 'info' : 'warning'}
      icon={<ReplayIcon />}
      sx={{ mb: 2, mt: 2 }}
    >
      <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 0.5 }}>
        Retry Handling
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {recovered
          ? `Transient failure recovered after ${retrySteps.length} retry attempt(s).`
          : `Failed after ${retrySteps.length} retry attempt(s).`}
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
        <Chip size="small" label={`${retrySteps.length || retryCount} retries`} color="warning" variant="outlined" />
        {meta?.maxAttempts != null && (
          <Chip size="small" label={`Max ${meta.maxAttempts} attempts`} variant="outlined" />
        )}
        {meta?.backoffMs != null && (
          <Chip size="small" label={`Backoff ${meta.backoffMs}ms`} variant="outlined" />
        )}
        {recovered && <Chip size="small" label="Recovered" color="success" />}
      </Box>
      {retrySteps.map((step) => {
        const stepMeta = parseRetryMeta(step);
        return (
          <Typography key={step.id || step.step_number} variant="caption" display="block" sx={{ mt: 0.5 }}>
            Step {step.step_number}: attempt {stepMeta?.nextAttempt ?? '?'} — {stepMeta?.reason || step.description}
          </Typography>
        );
      })}
    </Alert>
  );
}
