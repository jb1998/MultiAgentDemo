from dataclasses import dataclass
from typing import Protocol

from app.agents.trace.models import ExecutionTrace


@dataclass
class WorkflowResult:
    result: str
    tool_names: str
    duration_ms: int


class Workflow(Protocol):
    """Execution strategy — each workflow implements one agentic pattern."""

    async def run(
        self,
        task_text: str,
        trace: ExecutionTrace,
        stream_delay: float = 0,
    ) -> WorkflowResult: ...
