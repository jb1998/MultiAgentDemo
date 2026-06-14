from dataclasses import dataclass

from app.agents.trace.models import ExecutionTrace, StepCallback


@dataclass
class RunResult:
    trace: ExecutionTrace
    result: str | None = None
    tool_name: str = ""
    duration_ms: int = 0
    success: bool = True
    error: str | None = None
    retry_count: int = 0


STREAM_STEP_DELAY_SEC = 0.22
