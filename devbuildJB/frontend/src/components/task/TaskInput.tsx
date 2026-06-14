import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import BlockIcon from '@mui/icons-material/Block';
import SendIcon from '@mui/icons-material/Send';
import ShieldIcon from '@mui/icons-material/Shield';
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';
import AltRouteIcon from '@mui/icons-material/AltRoute';
import { motion } from 'framer-motion';
import { useEffect, useMemo, useState } from 'react';
import { submitTaskStream } from '../../services/taskStreamService';
import { getTools } from '../../services/taskService';
import { useAuthStore, useTaskStore } from '../../store/authStore';
import type { ExecutionStep, TaskMode, Tool } from '../../types/task.types';
import { detectInjection, detectPii } from '../../utils/securityUtils';
import { parseTaskLines } from '../../utils/smartRouting';
import ExecutionTrace from './ExecutionTrace';
import TaskResult from './TaskResult';
import WorkflowDiagram from './WorkflowDiagram';
import ConfidencePanel from './ConfidencePanel';
import DistributedTraceView from './DistributedTraceView';
import RetryPanel from './RetryPanel';
import SmartRoutingPanel from './SmartRoutingPanel';

const SMART_MULTI_EXAMPLE = `Calculate 15 + 20
What is the weather in Tokyo?
Convert "hello world" to uppercase`;

const toolExamples: { tool: string; example: string }[] = [
  { tool: 'TextProcessor', example: 'Convert "hello world" to uppercase' },
  { tool: 'Calculator', example: 'Calculate 15 * 23 + 100' },
  { tool: 'WeatherMock', example: 'What is the weather in Tokyo?' },
  { tool: 'WeatherMock (retry)', example: 'What is the weather in London?' },
  { tool: 'DateTimeTool', example: 'What is the current time?' },
  { tool: 'JSONProcessorTool', example: 'Format JSON {"name":"Demo","active":true}' },
  { tool: 'UnitConverterTool', example: 'Convert 100 km to miles' },
  { tool: 'Smart multi-tool', example: SMART_MULTI_EXAMPLE },
  { tool: 'Chain calc+text', example: 'Calculate 10*2 and convert to uppercase' },
];

function getApiErrorMessage(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const resp = (err as { response?: { status?: number; data?: { detail?: string } } }).response;
    if (resp?.status === 429) {
      return resp.data?.detail || 'Quota finished. Access blocked.';
    }
    if (resp?.data?.detail) return resp.data.detail;
  }
  if (err instanceof Error) return err.message;
  return 'Failed to submit task';
}

function resolveMode(uiMode: TaskMode, text: string): TaskMode {
  if (uiMode === 'smart_multi') return 'smart_multi';
  if (uiMode === 'single') return 'single';
  return parseTaskLines(text).length >= 2 ? 'smart_multi' : 'auto';
}

export default function TaskInput() {
  const { role } = useAuthStore();
  const isAdmin = role === 'admin';
  const [text, setText] = useState('');
  const [taskMode, setTaskMode] = useState<TaskMode>('single');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tools, setTools] = useState<Tool[]>([]);
  const [liveSteps, setLiveSteps] = useState<ExecutionStep[]>([]);
  const [retryCount, setRetryCount] = useState(0);
  const [streaming, setStreaming] = useState(false);
  const { currentTask, setCurrentTask } = useTaskStore();

  const lineCount = useMemo(() => parseTaskLines(text).length, [text]);
  const injectionBlocked = useMemo(() => detectInjection(text), [text]);
  const piiBlocked = useMemo(() => detectPii(text).detected, [text]);
  const submitBlocked = injectionBlocked || piiBlocked;
  const smartMultiInvalid = taskMode === 'smart_multi' && (lineCount < 2 || lineCount > 3);

  useEffect(() => {
    getTools().then(setTools).catch(() => {});
  }, []);

  const handleSubmit = async () => {
    if (!text.trim() || submitBlocked || smartMultiInvalid) return;
    setLoading(true);
    setStreaming(true);
    setError('');
    setLiveSteps([]);
    setRetryCount(0);
    setCurrentTask(null);

    const mode = resolveMode(taskMode, text.trim());

    try {
      const task = await submitTaskStream(text.trim(), mode, (event) => {
        if (event.type === 'step' && event.step) {
          setLiveSteps((prev) => {
            const exists = prev.some(
              (s) => s.step_number === event.step!.step_number && s.step_type === event.step!.step_type,
            );
            if (exists) return prev;
            return [...prev, event.step!];
          });
        }
        if (event.type === 'complete') {
          setRetryCount(event.retry_count ?? 0);
        }
      });
      setCurrentTask(task);
    } catch (e: unknown) {
      setError(getApiErrorMessage(e));
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  };

  const handleTextChange = (value: string) => {
    setText(value);
    setError('');
  };

  const showWorkflow =
    currentTask &&
    currentTask.execution_steps.filter((s) => s.step_type === 'execution' && s.tool_name).length >= 2;

  return (
    <Box>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Paper sx={{ p: 4, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <TipsAndUpdatesIcon color="primary" />
            <Typography variant="h5" fontWeight={600}>
              Submit a Task
            </Typography>
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Single mode: one task, one tool. Multi-tool mode: enter 2–3 tasks (one per line) and smart
            routing picks Calculator, TextProcessor, WeatherMock, etc. for each line.
          </Typography>

          <ToggleButtonGroup
            value={taskMode}
            exclusive
            onChange={(_, v) => v && setTaskMode(v)}
            size="small"
            sx={{ mb: 2 }}
            disabled={loading}
          >
            <ToggleButton value="single">Single Task</ToggleButton>
            <ToggleButton value="smart_multi">
              <AltRouteIcon sx={{ mr: 0.5, fontSize: 18 }} />
              Multi-Tool (Smart Routing)
            </ToggleButton>
          </ToggleButtonGroup>

          <TextField
            fullWidth
            multiline
            minRows={taskMode === 'smart_multi' ? 5 : 4}
            maxRows={10}
            placeholder={
              taskMode === 'smart_multi'
                ? 'Line 1: Calculate 15 + 20\nLine 2: What is the weather in Tokyo?\nLine 3: Convert "hello" to uppercase'
                : 'Try: Calculate 10*2 and convert to uppercase'
            }
            value={text}
            onChange={(e) => handleTextChange(e.target.value)}
            disabled={loading}
            error={submitBlocked || smartMultiInvalid}
            inputProps={{ maxLength: 5000 }}
            helperText={
              smartMultiInvalid
                ? `Multi-tool mode needs 2–3 lines (currently ${lineCount})`
                : `${text.length} / 5000${taskMode === 'smart_multi' ? ` · ${lineCount} line(s)` : ''}`
            }
            color={submitBlocked || smartMultiInvalid ? 'error' : 'primary'}
          />

          {taskMode === 'smart_multi' && lineCount >= 2 && lineCount <= 3 && (
            <SmartRoutingPanel text={text} />
          )}

          {injectionBlocked && (
            <Alert severity="error" icon={<BlockIcon />} sx={{ mt: 2 }}>
              <Typography variant="subtitle2" fontWeight={600}>
                Prompt Injection Blocked
              </Typography>
              Prompt injection detected. This request has been blocked.
            </Alert>
          )}

          {piiBlocked && !injectionBlocked && (
            <Alert severity="warning" icon={<ShieldIcon />} sx={{ mt: 2 }}>
              <Typography variant="subtitle2" fontWeight={600}>
                PII Detected
              </Typography>
              Delete PII information and try again.
            </Alert>
          )}

          <Typography variant="body2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            Try an example:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1, mb: 3 }}>
            {toolExamples.map(({ tool, example }) => (
              <Chip
                key={tool}
                label={tool}
                title={example}
                size="small"
                onClick={() => {
                  handleTextChange(example);
                  if (tool === 'Smart multi-tool') setTaskMode('smart_multi');
                  if (tool === 'Chain calc+text') setTaskMode('single');
                }}
                sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'rgba(200, 16, 46, 0.1)', color: 'primary.main' } }}
              />
            ))}
          </Box>

          <Button
            variant="contained"
            size="large"
            endIcon={
              loading ? (
                <CircularProgress size={20} color="inherit" />
              ) : submitBlocked || smartMultiInvalid ? (
                <BlockIcon />
              ) : (
                <SendIcon />
              )
            }
            onClick={handleSubmit}
            disabled={loading || !text.trim() || submitBlocked || smartMultiInvalid}
            className={loading ? 'pulse-glow' : ''}
            color={submitBlocked || smartMultiInvalid ? 'error' : 'primary'}
          >
            {submitBlocked || smartMultiInvalid
              ? 'Blocked'
              : loading
                ? 'Streaming agent steps...'
                : taskMode === 'smart_multi'
                  ? 'Run Smart Routing'
                  : 'Run Agent'}
          </Button>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </Paper>
      </motion.div>

      {tools.length > 0 && (
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 3 }}>
          {tools.map((t) => (
            <Chip key={t.name} label={t.name} variant="outlined" title={t.description} />
          ))}
        </Box>
      )}

      {streaming && !isAdmin && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Agent running… {liveSteps.length > 0 ? `${liveSteps.length} steps completed` : 'starting'}
        </Alert>
      )}

      {streaming && isAdmin && (
        <>
          <RetryPanel steps={liveSteps} retryCount={retryCount} />
          <ExecutionTrace steps={liveSteps} live />
        </>
      )}

      {currentTask && (
        <>
          {isAdmin && showWorkflow && (
            <WorkflowDiagram steps={currentTask.execution_steps} result={currentTask.result} />
          )}
          {isAdmin && !streaming && (
            <SmartRoutingPanel steps={currentTask.execution_steps} />
          )}
          {isAdmin && !streaming && <DistributedTraceView steps={currentTask.execution_steps} />}
          {isAdmin && !streaming && <ConfidencePanel steps={currentTask.execution_steps} />}
          {isAdmin && !streaming && (
            <RetryPanel steps={currentTask.execution_steps} retryCount={retryCount} />
          )}
          <TaskResult task={currentTask} />
          {isAdmin && !streaming && <ExecutionTrace steps={currentTask.execution_steps} />}
        </>
      )}
    </Box>
  );
}
