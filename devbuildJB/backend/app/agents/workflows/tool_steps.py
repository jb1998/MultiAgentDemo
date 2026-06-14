"""Shared tool selection + execution trace steps."""

import json
from typing import Any

from app.agents.retry.executor import RetryExecutor
from app.agents.selection.tool_selector import ToolSelector
from app.agents.trace.models import ExecutionTrace
from app.tools.base_tool import CONFIDENCE_THRESHOLD, Tool


class ToolStepRunner:
    """Records selection and execution steps for a single tool invocation."""

    @staticmethod
    async def record_selection(
        trace: ExecutionTrace,
        tool: Tool,
        confidence: float,
        all_scores: list[tuple[str, float]],
        stream_delay: float,
        details: str | None = None,
        extra: dict | None = None,
    ) -> None:
        payload = {
            "confidence": confidence,
            "selected_tool": tool.name,
            "all_scores": [{"tool": name, "score": score} for name, score in all_scores],
            "threshold": CONFIDENCE_THRESHOLD,
            "status": ToolSelector.confidence_status(confidence),
        }
        if extra:
            payload.update(extra)

        await trace.add_action_async(
            "Selected tool",
            details or tool.name,
            tool_name=tool.name,
            extra=payload,
            stream_delay=stream_delay,
        )

    @staticmethod
    async def execute(
        trace: ExecutionTrace,
        tool: Tool,
        task_text: str,
        stream_delay: float,
        execution_label: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        output, duration_ms = await RetryExecutor.execute_with_retry(
            tool.name,
            task_text,
            lambda: tool.execute(task_text),
            trace,
            stream_delay=0,
        )
        await trace.add_action_async(
            "Executed tool",
            execution_label or tool.name,
            tool_name=tool.name,
            input_data=task_text,
            output_data=json.dumps(output),
            duration_ms=duration_ms,
            stream_delay=stream_delay,
        )
        return output, duration_ms
