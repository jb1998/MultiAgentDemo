"""Top-level agent pipeline — thin orchestration over modular workflows."""

import json

from app.agents.analysis.task_analyzer import TaskAnalyzer
from app.agents.runner.models import RunResult, STREAM_STEP_DELAY_SEC
from app.agents.trace.models import ExecutionTrace, StepCallback
from app.agents.workflows.dispatcher import WorkflowDispatcher
from app.utils.exceptions import ToolExecutionError, ToolNotFoundError


class TaskRunner:
    async def run(
        self,
        task_text: str,
        mode: str = "auto",
        on_step: StepCallback | None = None,
        stream_delay: float = 0,
    ) -> RunResult:
        trace = ExecutionTrace(on_step=on_step)
        cleaned = (task_text or "").strip()

        if not cleaned:
            await trace.add_action_async(
                "Received task", "", input_data=task_text or "", stream_delay=stream_delay
            )
            await trace.add_action_async(
                "Tool execution failed", "Task text cannot be empty", stream_delay=stream_delay
            )
            return RunResult(trace=trace, success=False, error="Task text cannot be empty")

        await trace.add_action_async(
            "Received task", cleaned, input_data=cleaned, stream_delay=stream_delay
        )

        analysis = TaskAnalyzer.analyze(cleaned, mode=mode)
        await trace.add_action_async(
            "Analyzed task",
            analysis.summary,
            extra=analysis.to_dict(),
            stream_delay=stream_delay,
        )

        try:
            workflow_result = await WorkflowDispatcher.dispatch(
                cleaned, mode, trace, stream_delay
            )
            await trace.add_action_async(
                "Generated result",
                workflow_result.result,
                output_data=json.dumps({"result": workflow_result.result}),
                stream_delay=stream_delay,
            )
            return RunResult(
                trace=trace,
                result=workflow_result.result,
                tool_name=workflow_result.tool_names,
                duration_ms=workflow_result.duration_ms,
                success=True,
                retry_count=self._count_retries(trace),
            )
        except ToolNotFoundError as exc:
            if not any(s.action == "No suitable tool found" for s in trace.steps):
                await trace.add_action_async(
                    "No suitable tool found", cleaned[:200], stream_delay=stream_delay
                )
            return RunResult(
                trace=trace,
                success=False,
                error=str(exc),
                retry_count=self._count_retries(trace),
            )
        except ToolExecutionError as exc:
            if not any(s.action == "Tool execution failed" for s in trace.steps):
                await trace.add_action_async(
                    "Tool execution failed",
                    str(exc),
                    tool_name=self._last_tool_name(trace) or None,
                    stream_delay=stream_delay,
                )
            return RunResult(
                trace=trace,
                tool_name=self._last_tool_name(trace),
                duration_ms=self._total_duration(trace),
                success=False,
                error=str(exc),
                retry_count=self._count_retries(trace),
            )

    @staticmethod
    def _last_tool_name(trace: ExecutionTrace) -> str:
        for step in reversed(trace.steps):
            if step.tool_name:
                return step.tool_name
        return ""

    @staticmethod
    def _total_duration(trace: ExecutionTrace) -> int:
        return sum(s.duration_ms or 0 for s in trace.steps)

    @staticmethod
    def _count_retries(trace: ExecutionTrace) -> int:
        return sum(1 for s in trace.steps if s.step_type == "retry")
