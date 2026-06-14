"""Smart multi-line routing — each line routed to its best tool."""

from app.agents.routing.smart_router import SmartRouter
from app.agents.trace.models import ExecutionTrace
from app.agents.workflows.base import WorkflowResult
from app.agents.workflows.tool_steps import ToolStepRunner


class SmartMultiWorkflow:
    async def run(
        self,
        task_text: str,
        trace: ExecutionTrace,
        stream_delay: float = 0,
    ) -> WorkflowResult:
        plan = SmartRouter.build_plan(task_text)
        tool_names: list[str] = []
        result_lines: list[str] = []
        total_duration = 0

        plan_summary = ", ".join(f"{r.tool.name} ({r.intent})" for r in plan)
        await trace.add_action_async(
            "Smart routing",
            f"Planned {len(plan)} tools: {plan_summary}",
            step_type="workflow",
            extra={
                "workflow_type": "smart_multi",
                "routing_plan": [r.to_dict() for r in plan],
                "subtask_count": len(plan),
            },
            stream_delay=stream_delay,
        )

        for routed in plan:
            tool_names.append(routed.tool.name)
            await ToolStepRunner.record_selection(
                trace,
                routed.tool,
                routed.confidence,
                routed.all_scores,
                stream_delay,
                details=f"Task {routed.index}: {routed.tool.name} ({routed.intent})",
                extra={
                    "subtask_index": routed.index,
                    "subtask_text": routed.task_text,
                    "intent": routed.intent,
                },
            )
            output, duration_ms = await ToolStepRunner.execute(
                trace,
                routed.tool,
                routed.task_text,
                stream_delay,
                execution_label=f"Task {routed.index}: {routed.tool.name}",
            )
            total_duration += duration_ms
            result_value = output.get("result", str(output))
            result_lines.append(
                f"{routed.index}. [{routed.tool.name}] {routed.task_text} → {result_value}"
            )

        final = "Smart routing results:\n" + "\n".join(result_lines)
        return WorkflowResult(
            result=final,
            tool_names=" + ".join(dict.fromkeys(tool_names)),
            duration_ms=total_duration,
        )
