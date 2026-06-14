from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.models.schemas import (
    AuditLogResponse,
    CostRecordResponse,
    CostSummaryResponse,
    MetricsResponse,
    TaskListResponse,
    ToolMetadata,
    UserResponse,
)
from app.models.task import User
from app.persistence.database import get_db
from app.persistence.repositories.task_repository import TaskRepository, UserRepository
from app.tools.tool_registry import tool_registry

router = APIRouter(tags=["tools"])


@router.get("/tools", response_model=list[ToolMetadata])
async def list_tools():
    return [ToolMetadata(**t.get_metadata()) for t in tool_registry.list_tools()]


admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    repo = TaskRepository(db)
    data = await repo.get_metrics()
    return MetricsResponse(**data)


@admin_router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    repo = UserRepository(db)
    users = await repo.list_all()
    return [UserResponse.model_validate(u) for u in users]


@admin_router.get("/tasks", response_model=TaskListResponse)
async def list_all_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    repo = TaskRepository(db)
    tasks, total = await repo.list_tasks(None, page, page_size, search)
    return TaskListResponse(tasks=tasks, total=total, page=page, page_size=page_size)


@admin_router.get("/logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    repo = TaskRepository(db)
    logs = await repo.get_audit_logs(limit)
    return [AuditLogResponse.model_validate(log) for log in logs]


@admin_router.get("/costs", response_model=CostSummaryResponse)
async def get_cost_summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    repo = TaskRepository(db)
    data = await repo.get_cost_summary()
    return CostSummaryResponse(
        total_cost_usd=data["total_cost_usd"],
        tool_costs=data["tool_costs"],
        service_costs=data["service_costs"],
        recent_records=[CostRecordResponse.model_validate(r) for r in data["recent_records"]],
    )
