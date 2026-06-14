from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_admin
from app.api.rate_limit import limiter
from app.models.schemas import TaskCreate, TaskListResponse, TaskResponse
from app.models.task import Task, User
from app.orchestration.controller import AgentController
from app.observability.tracer import DistributedTracer
from app.persistence.database import get_db
from app.persistence.repositories.task_repository import TaskRepository
from app.security.auth import detect_injection, detect_pii
from app.services.quota_service import get_user_quota, is_quota_exceeded

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _to_task_response(task: Task, user: User) -> TaskResponse:
    resp = TaskResponse.model_validate(task)
    if user.role != "admin":
        resp.execution_steps = []
    return resp


async def _validate_task_submission(
    repo: TaskRepository,
    current_user: User,
    task_text: str,
) -> None:
    quota = get_user_quota(current_user.username)
    if quota is not None:
        count = await repo.count_user_tasks(current_user.id)
        if is_quota_exceeded(current_user.username, count):
            await repo.log_security_event(
                event_type="quota_exceeded",
                user_id=current_user.id,
                details=f"User {current_user.username} exceeded quota of {quota}",
            )
            await repo.log_audit(
                action="quota_blocked",
                message=f"User {current_user.username} quota finished — access blocked ({count}/{quota} tasks used)",
                user_id=current_user.id,
                username=current_user.username,
                level="warning",
            )
            raise HTTPException(
                status_code=429,
                detail="Quota finished. Access blocked. You have used all 5 allowed task submissions.",
            )

    if detect_injection(task_text):
        await repo.log_security_event(
            event_type="injection_blocked",
            user_id=current_user.id,
            details=task_text[:200],
        )
        await repo.log_audit(
            action="injection_blocked",
            message="Prompt injection blocked",
            user_id=current_user.id,
            username=current_user.username,
            level="warning",
        )
        raise HTTPException(
            status_code=400,
            detail="Prompt injection detected. This request has been blocked.",
        )

    has_pii, _ = detect_pii(task_text)
    if has_pii:
        await repo.log_audit(
            action="pii_blocked",
            message="PII detected — submission blocked",
            user_id=current_user.id,
            username=current_user.username,
            level="warning",
        )
        raise HTTPException(
            status_code=400,
            detail="PII Detected. Delete PII information and try again.",
        )


@router.post("", response_model=TaskResponse)
@limiter.limit("30/minute")
async def submit_task(
    request: Request,
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = TaskRepository(db)
    await _validate_task_submission(repo, current_user, payload.task_text)

    tracer = DistributedTracer()
    task = await repo.create(
        user_id=current_user.id, task_text=payload.task_text.strip(), trace_id=tracer.trace_id
    )

    await repo.log_audit(
        action="task_submitted",
        message=f"Task #{task.id} submitted by {current_user.username}",
        user_id=current_user.id,
        username=current_user.username,
    )

    controller = AgentController(db)
    await controller.process_task(task.id, username=current_user.username, mode=payload.mode)

    task = await repo.get_by_id(task.id)
    await db.refresh(task, attribute_names=["execution_steps"])
    return _to_task_response(task, current_user)


@router.post("/stream")
@limiter.limit("30/minute")
async def stream_task(
    request: Request,
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a task and stream agent steps in real-time via Server-Sent Events."""
    repo = TaskRepository(db)
    await _validate_task_submission(repo, current_user, payload.task_text)

    tracer = DistributedTracer()
    task = await repo.create(
        user_id=current_user.id, task_text=payload.task_text.strip(), trace_id=tracer.trace_id
    )

    await repo.log_audit(
        action="task_submitted",
        message=f"Task #{task.id} submitted (stream) by {current_user.username}",
        user_id=current_user.id,
        username=current_user.username,
    )

    controller = AgentController(db)
    is_admin = current_user.role == "admin"

    async def event_generator():
        async for chunk in controller.stream_task(
            task.id,
            username=current_user.username,
            include_full_steps=is_admin,
            mode=payload.mode,
        ):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = TaskRepository(db)
    user_id = None if current_user.role == "admin" else current_user.id
    tasks, total = await repo.list_tasks(user_id, page, page_size, search)
    return TaskListResponse(
        tasks=[_to_task_response(t, current_user) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = TaskRepository(db)
    task = await repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_response(task, current_user)


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    repo = TaskRepository(db)
    deleted = await repo.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    await repo.log_audit(
        action="task_deleted",
        message=f"Admin deleted task #{task_id}",
        user_id=current_user.id,
        username=current_user.username,
        level="warning",
    )
    return {"message": "Task deleted successfully"}


@router.get("/{task_id}/trace", response_model=TaskResponse)
async def get_task_trace(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    repo = TaskRepository(db)
    task = await repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task)
