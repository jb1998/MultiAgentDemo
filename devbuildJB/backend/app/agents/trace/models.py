"""Execution trace models and step emission."""

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

StepCallback = Callable[["TraceStep"], Awaitable[None] | None]

ACTION_STEP_TYPES: dict[str, str] = {
    "Received task": "input",
    "Analyzed task": "analyze",
    "Selected tool": "tool_selection",
    "Executed tool": "execution",
    "Generated result": "output",
    "Persisted task": "persist",
    "Tool execution failed": "error",
    "No suitable tool found": "error",
    "Retrying tool": "retry",
    "Smart routing": "workflow",
}


@dataclass
class TraceStep:
    step_number: int
    step_type: str
    description: str
    action: str | None = None
    tool_name: str | None = None
    input_data: str | None = None
    output_data: str | None = None
    duration_ms: int | None = None


@dataclass
class ExecutionTrace:
    steps: list[TraceStep] = field(default_factory=list)
    on_step: StepCallback | None = None

    async def _emit(self, step: TraceStep, stream_delay: float = 0) -> None:
        if self.on_step:
            result = self.on_step(step)
            if asyncio.iscoroutine(result):
                await result
        if stream_delay > 0:
            await asyncio.sleep(stream_delay)

    async def add_action_async(
        self,
        action: str,
        details: str | None = None,
        step_type: str | None = None,
        tool_name: str | None = None,
        input_data: str | None = None,
        output_data: str | None = None,
        duration_ms: int | None = None,
        extra: dict | None = None,
        stream_delay: float = 0,
    ) -> TraceStep:
        resolved_type = step_type or ACTION_STEP_TYPES.get(action, "trace")
        payload: dict = {"action": action}
        if details is not None:
            payload["details"] = details
        if extra:
            payload.update(extra)

        description = action
        if details:
            description = f"{action}: {details}"

        merged_output = output_data if output_data is not None else json.dumps(payload)

        step = TraceStep(
            step_number=len(self.steps) + 1,
            step_type=resolved_type,
            description=description,
            action=action,
            tool_name=tool_name,
            input_data=input_data,
            output_data=merged_output,
            duration_ms=duration_ms,
        )
        self.steps.append(step)
        await self._emit(step, stream_delay)
        return step

    async def add_async(
        self,
        step_type: str,
        description: str,
        tool_name: str | None = None,
        input_data: str | None = None,
        output_data: str | None = None,
        duration_ms: int | None = None,
        stream_delay: float = 0,
    ) -> TraceStep:
        step = TraceStep(
            step_number=len(self.steps) + 1,
            step_type=step_type,
            description=description,
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
        )
        self.steps.append(step)
        await self._emit(step, stream_delay)
        return step

    def to_action_list(self) -> list[dict]:
        results: list[dict] = []
        for step in self.steps:
            details = None
            if step.output_data:
                try:
                    details = json.loads(step.output_data).get("details")
                except json.JSONDecodeError:
                    details = None
            results.append(
                {
                    "step": step.step_number,
                    "action": step.action or step.description,
                    "details": details,
                }
            )
        return results
