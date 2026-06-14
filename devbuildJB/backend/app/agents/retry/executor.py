"""Retry transient tool failures with visible trace steps."""

import asyncio
import time
from collections.abc import Callable
from typing import Any

from app.agents.retry.context import MAX_RETRIES, RETRY_BACKOFF_SEC, retry_attempt_ctx
from app.agents.trace.models import ExecutionTrace
from app.utils.exceptions import ToolExecutionError, TransientToolError


class RetryExecutor:
    @staticmethod
    def is_retryable(exc: BaseException) -> bool:
        return isinstance(exc, TransientToolError)

    @staticmethod
    async def execute_with_retry(
        tool_name: str,
        task_text: str,
        execute_fn: Callable[[], dict[str, Any]],
        trace: ExecutionTrace,
        stream_delay: float = 0,
    ) -> tuple[dict[str, Any], int]:
        total_ms = 0
        last_error: str | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            retry_attempt_ctx.set(attempt)
            start = time.perf_counter()
            try:
                output = execute_fn()
                total_ms += int((time.perf_counter() - start) * 1000)
                return output, total_ms
            except Exception as exc:
                total_ms += int((time.perf_counter() - start) * 1000)
                last_error = str(exc)
                if not RetryExecutor.is_retryable(exc) or attempt >= MAX_RETRIES:
                    raise ToolExecutionError(last_error) from exc

                await trace.add_action_async(
                    "Retrying tool",
                    f"Attempt {attempt + 1} of {MAX_RETRIES} — {last_error}",
                    step_type="retry",
                    tool_name=tool_name,
                    extra={
                        "attempt": attempt,
                        "next_attempt": attempt + 1,
                        "max_attempts": MAX_RETRIES,
                        "reason": last_error,
                        "backoff_ms": int(RETRY_BACKOFF_SEC * 1000),
                    },
                    stream_delay=stream_delay,
                )
                await asyncio.sleep(RETRY_BACKOFF_SEC)

        raise ToolExecutionError(last_error or "Tool execution failed")
