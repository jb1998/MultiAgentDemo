"""Single-tool workflow — one task, one tool."""

from app.agents.selection.tool_selector import ToolSelector
from app.agents.trace.models import ExecutionTrace
from app.agents.workflows.base import WorkflowResult
from app.agents.workflows.tool_steps import ToolStepRunner


class SingleToolWorkflow:
    async def run(
        self,
        task_text: str,
        trace: ExecutionTrace,
        stream_delay: float = 0,
    ) -> WorkflowResult:
        tool, confidence, all_scores = ToolSelector.select(task_text)
        await ToolStepRunner.record_selection(trace, tool, confidence, all_scores, stream_delay)
        output, duration_ms = await ToolStepRunner.execute(trace, tool, task_text, stream_delay)
        result = output.get("result", str(output))
        return WorkflowResult(result=result, tool_names=tool.name, duration_ms=duration_ms)
