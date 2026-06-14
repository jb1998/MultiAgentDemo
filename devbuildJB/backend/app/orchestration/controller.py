import asyncio
import json

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import ExecutionStepResponse, TaskResponse
from app.models.task import ExecutionStep, Task, TaskStatus
from app.observability.tracer import DistributedTracer
from app.agents.runner import STREAM_STEP_DELAY_SEC, RunResult, TaskRunner
from app.persistence.repositories.task_repository import TaskRepository
from app.services.cost_tracker import infra_costs_for_request, tool_call_cost
from app.utils.exceptions import DatabaseError


def format_sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


def step_to_dict(step: ExecutionStep) -> dict:
    return ExecutionStepResponse.model_validate(step).model_dump(mode="json")


class AgentController:
    """
    Orchestrates the full task lifecycle:
    parse → trace → select tool → execute → persist → respond.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TaskRepository(session)
        self.runner = TaskRunner()

    async def process_task(
        self,
        task_id: int,
        username: str | None = None,
        mode: str = "auto",
    ) -> None:
        task = await self.repo.get_by_id(task_id)
        if not task:
            return

        tracer = DistributedTracer()
        tracer.start_layer("API Gateway")
        tracer.end_layer("API Gateway", "JWT validated, rate-limit checked")

        await self.repo.update_status(task, TaskStatus.PROCESSING.value)

        tracer.start_layer("Orchestrator")
        tracer.end_layer("Orchestrator", f"Task #{task_id} dispatched to agent")
        tracer.start_layer("Agent Layer")

        run_result = await self.runner.run(task.task_text, mode=mode, stream_delay=0)

        tracer.end_layer("Agent Layer", f"Tool: {run_result.tool_name or 'none'}")
        tracer.start_layer("Tool Execution")

        try:
            tracer.end_layer(
                "Tool Execution",
                f"{run_result.tool_name or 'none'} in {run_result.duration_ms}ms",
            )
            tracer.start_layer("Response")
            await self._finalize_task(task, run_result, tracer, username, stream_persisted=False)
        except SQLAlchemyError as exc:
            raise DatabaseError(f"Database error while persisting task: {exc}") from exc

    async def stream_task(
        self,
        task_id: int,
        username: str | None = None,
        include_full_steps: bool = True,
        mode: str = "auto",
    ):
        """Async generator yielding SSE events as agent steps execute."""
        task = await self.repo.get_by_id(task_id)
        if not task:
            yield format_sse({"type": "error", "error": "Task not found"})
            return

        queue: asyncio.Queue = asyncio.Queue()
        tracer = DistributedTracer()
        tracer.start_layer("API Gateway")
        tracer.end_layer("API Gateway", "JWT validated, rate-limit checked")

        async def on_step(trace_step) -> None:
            db_step = await self.repo.add_step(
                task_id=task.id,
                step_number=trace_step.step_number,
                step_type=trace_step.step_type,
                description=trace_step.description,
                tool_name=trace_step.tool_name,
                input_data=trace_step.input_data,
                output_data=trace_step.output_data,
                duration_ms=trace_step.duration_ms,
            )
            await self.session.commit()
            payload: dict = {"type": "step", "step": step_to_dict(db_step)}
            if not include_full_steps:
                payload["step"] = {
                    "step_number": db_step.step_number,
                    "step_type": db_step.step_type,
                    "description": db_step.description,
                }
            await queue.put(payload)

        async def run_agent() -> RunResult | None:
            try:
                await self.repo.update_status(task, TaskStatus.PROCESSING.value)
                await self.session.commit()
                await queue.put({
                    "type": "status",
                    "status": "processing",
                    "task_id": task_id,
                    "message": "Agent started",
                })

                tracer.start_layer("Orchestrator")
                tracer.end_layer("Orchestrator", f"Task #{task_id} dispatched to agent")
                tracer.start_layer("Agent Layer")

                result = await self.runner.run(
                    task.task_text,
                    mode=mode,
                    on_step=on_step,
                    stream_delay=STREAM_STEP_DELAY_SEC,
                )

                tracer.end_layer("Agent Layer", f"Tool: {result.tool_name or 'none'}")
                tracer.start_layer("Tool Execution")
                tracer.end_layer(
                    "Tool Execution",
                    f"{result.tool_name or 'none'} in {result.duration_ms}ms",
                )
                tracer.start_layer("Response")
                return result
            except Exception as exc:
                await queue.put({"type": "error", "error": str(exc)})
                return None

        agent_task = asyncio.create_task(run_agent())

        while True:
            if agent_task.done() and queue.empty():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.15)
            except asyncio.TimeoutError:
                if agent_task.done():
                    break
                continue

            yield format_sse(event)

        run_result = await agent_task
        if run_result is None:
            return

        try:
            await self._finalize_task(
                task,
                run_result,
                tracer,
                username,
                stream_persisted=True,
            )
            refreshed = await self.repo.get_by_id(task_id)
            task_response = TaskResponse.model_validate(refreshed)
            if not include_full_steps:
                task_response.execution_steps = []

            yield format_sse({
                "type": "complete",
                "task": task_response.model_dump(mode="json"),
                "retry_count": run_result.retry_count,
            })
        except SQLAlchemyError as exc:
            yield format_sse({"type": "error", "error": f"Database error: {exc}"})

    async def _finalize_task(
        self,
        task: Task,
        run_result: RunResult,
        tracer: DistributedTracer,
        username: str | None,
        stream_persisted: bool,
    ) -> None:
        await run_result.trace.add_action_async("Persisted task", f"Task #{task.id}")

        if stream_persisted:
            last_step = run_result.trace.steps[-1]
            await self.repo.add_step(
                task_id=task.id,
                step_number=last_step.step_number,
                step_type=last_step.step_type,
                description=last_step.description,
                tool_name=last_step.tool_name,
                input_data=last_step.input_data,
                output_data=last_step.output_data,
                duration_ms=last_step.duration_ms,
            )
        else:
            await self._persist_trace(task.id, run_result.trace)

        dist_trace = tracer.finalize(run_result.duration_ms)
        task.trace_id = dist_trace.trace_id
        await self.repo.add_step(
            task_id=task.id,
            step_number=len(run_result.trace.steps) + 1,
            step_type="distributed_trace",
            description=f"Distributed trace {dist_trace.trace_id} — bottleneck: {dist_trace.bottleneck}",
            output_data=dist_trace.to_json(),
            duration_ms=dist_trace.total_ms,
        )

        if run_result.success:
            await self._record_usage_and_costs(task.id, run_result)
            tracer.end_layer("Response", "TaskResponse serialized")
            await self.repo.update_status(task, TaskStatus.COMPLETED.value, result=run_result.result)
            await self.repo.log_audit(
                action="task_completed",
                message=f"Task #{task.id} completed via {run_result.tool_name} in {run_result.duration_ms}ms",
                username=username,
                metadata_json=dist_trace.to_json(),
            )
        else:
            error_payload = json.dumps({"error": run_result.error})
            tracer.end_layer("Response", f"Error: {run_result.error}")
            await self.repo.update_status(task, TaskStatus.FAILED.value, result=error_payload)
            await self.repo.log_audit(
                action="task_failed",
                message=f"Task #{task.id} failed: {run_result.error}",
                username=username,
                level="error",
            )

        await self.session.commit()

    async def _persist_trace(self, task_id: int, trace) -> None:
        for step in trace.steps:
            await self.repo.add_step(
                task_id=task_id,
                step_number=step.step_number,
                step_type=step.step_type,
                description=step.description,
                tool_name=step.tool_name,
                input_data=step.input_data,
                output_data=step.output_data,
                duration_ms=step.duration_ms,
            )

    async def _record_usage_and_costs(self, task_id: int, run_result: RunResult) -> None:
        execution_steps = [
            s for s in run_result.trace.steps
            if s.step_type == "execution" and s.tool_name
        ]
        if execution_steps:
            for step in execution_steps:
                await self.repo.add_tool_usage(
                    task_id=task_id,
                    tool_name=step.tool_name or run_result.tool_name,
                    execution_time_ms=step.duration_ms or 0,
                    success=True,
                )
                await self.repo.record_cost(
                    service_name=f"Tool: {step.tool_name}",
                    cost_usd=tool_call_cost(step.tool_name or run_result.tool_name),
                    task_id=task_id,
                    tool_name=step.tool_name,
                    duration_ms=step.duration_ms,
                )
        elif run_result.tool_name:
            await self.repo.add_tool_usage(
                task_id=task_id,
                tool_name=run_result.tool_name,
                execution_time_ms=run_result.duration_ms,
                success=True,
            )
            await self.repo.record_cost(
                service_name=f"Tool: {run_result.tool_name}",
                cost_usd=tool_call_cost(run_result.tool_name.split(" + ")[0]),
                task_id=task_id,
                tool_name=run_result.tool_name,
                duration_ms=run_result.duration_ms,
            )

        for svc, cost in infra_costs_for_request().items():
            await self.repo.record_cost(
                service_name=svc,
                cost_usd=cost,
                task_id=task_id,
            )
