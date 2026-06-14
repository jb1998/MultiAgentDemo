from datetime import datetime, timezone

from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import AuditLog, CostRecord, ExecutionStep, SecurityEvent, Task, TaskStatus, ToolUsage, User


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, task_text: str, trace_id: str | None = None) -> Task:
        task = Task(
            user_id=user_id,
            task_text=task_text,
            status=TaskStatus.PENDING.value,
            trace_id=trace_id,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_by_id(self, task_id: int) -> Task | None:
        result = await self.session.execute(
            select(Task)
            .options(selectinload(Task.execution_steps))
            .where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_tasks(
        self, user_id: int | None, page: int = 1, page_size: int = 20, search: str | None = None
    ) -> tuple[list[Task], int]:
        query = select(Task).options(selectinload(Task.execution_steps))
        count_query = select(func.count(Task.id))

        if user_id is not None:
            query = query.where(Task.user_id == user_id)
            count_query = count_query.where(Task.user_id == user_id)
        if search:
            query = query.where(Task.task_text.ilike(f"%{search}%"))
            count_query = count_query.where(Task.task_text.ilike(f"%{search}%"))

        total = (await self.session.execute(count_query)).scalar() or 0
        query = query.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        tasks = (await self.session.execute(query)).scalars().all()
        return list(tasks), total

    async def update_status(
        self, task: Task, status: str, result: str | None = None
    ) -> Task:
        task.status = status
        if result is not None:
            task.result = result
        if status in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value):
            task.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return task

    async def add_step(
        self,
        task_id: int,
        step_number: int,
        step_type: str,
        description: str,
        tool_name: str | None = None,
        input_data: str | None = None,
        output_data: str | None = None,
        duration_ms: int | None = None,
    ) -> ExecutionStep:
        step = ExecutionStep(
            task_id=task_id,
            step_number=step_number,
            step_type=step_type,
            description=description,
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
        )
        self.session.add(step)
        await self.session.flush()
        return step

    async def add_tool_usage(
        self,
        task_id: int,
        tool_name: str,
        execution_time_ms: int,
        success: bool,
        error_message: str | None = None,
    ) -> ToolUsage:
        usage = ToolUsage(
            task_id=task_id,
            tool_name=tool_name,
            execution_time_ms=execution_time_ms,
            success=success,
            error_message=error_message,
        )
        self.session.add(usage)
        await self.session.flush()
        return usage

    async def delete_task(self, task_id: int) -> bool:
        task = await self.get_by_id(task_id)
        if not task:
            return False
        await self.session.delete(task)
        await self.session.flush()
        return True

    async def log_security_event(
        self, event_type: str, user_id: int | None = None, details: str | None = None
    ) -> SecurityEvent:
        event = SecurityEvent(event_type=event_type, user_id=user_id, details=details)
        self.session.add(event)
        await self.session.flush()
        return event

    async def log_audit(
        self,
        action: str,
        message: str,
        user_id: int | None = None,
        username: str | None = None,
        level: str = "info",
        metadata_json: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            message=message,
            level=level,
            metadata_json=metadata_json,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_audit_logs(self, limit: int = 100) -> list[AuditLog]:
        result = await self.session.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def count_user_tasks(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Task.id)).where(Task.user_id == user_id)
        )
        return result.scalar() or 0

    async def record_cost(
        self,
        service_name: str,
        cost_usd: float,
        task_id: int | None = None,
        tool_name: str | None = None,
        duration_ms: int | None = None,
    ) -> CostRecord:
        record = CostRecord(
            task_id=task_id,
            tool_name=tool_name,
            service_name=service_name,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_cost_summary(self) -> dict:
        total_cost = (
            await self.session.execute(select(func.sum(CostRecord.cost_usd)))
        ).scalar() or 0.0

        tool_rows = (
            await self.session.execute(
                select(CostRecord.tool_name, func.sum(CostRecord.cost_usd), func.count(CostRecord.id))
                .where(CostRecord.tool_name.isnot(None))
                .group_by(CostRecord.tool_name)
            )
        ).all()

        service_rows = (
            await self.session.execute(
                select(CostRecord.service_name, func.sum(CostRecord.cost_usd), func.count(CostRecord.id))
                .group_by(CostRecord.service_name)
            )
        ).all()

        recent = (
            await self.session.execute(
                select(CostRecord).order_by(CostRecord.created_at.desc()).limit(20)
            )
        ).scalars().all()

        return {
            "total_cost_usd": round(float(total_cost), 6),
            "tool_costs": {
                row[0]: {"total_usd": round(float(row[1]), 6), "calls": row[2]} for row in tool_rows
            },
            "service_costs": {
                row[0]: {"total_usd": round(float(row[1]), 6), "calls": row[2]} for row in service_rows
            },
            "recent_records": recent,
        }

    async def get_metrics(self) -> dict:
        total = (await self.session.execute(select(func.count(Task.id)))).scalar() or 0
        completed = (
            await self.session.execute(
                select(func.count(Task.id)).where(Task.status == TaskStatus.COMPLETED.value)
            )
        ).scalar() or 0
        failed = (
            await self.session.execute(
                select(func.count(Task.id)).where(Task.status == TaskStatus.FAILED.value)
            )
        ).scalar() or 0

        tool_rows = (
            await self.session.execute(
                select(ToolUsage.tool_name, func.count(ToolUsage.id)).group_by(ToolUsage.tool_name)
            )
        ).all()
        tool_success_rows = (
            await self.session.execute(
                select(
                    ToolUsage.tool_name,
                    func.avg(func.cast(ToolUsage.success, Integer)),
                ).group_by(ToolUsage.tool_name)
            )
        ).all()
        avg_ms = (
            await self.session.execute(select(func.avg(ToolUsage.execution_time_ms)))
        ).scalar() or 0.0

        total_steps = (
            await self.session.execute(select(func.count(ExecutionStep.id)))
        ).scalar() or 0
        step_type_rows = (
            await self.session.execute(
                select(ExecutionStep.step_type, func.count(ExecutionStep.id)).group_by(ExecutionStep.step_type)
            )
        ).all()

        pii_masked_tasks = (
            await self.session.execute(
                select(func.count(Task.id)).where(
                    Task.task_text.like("%[EMAIL]%")
                    | Task.task_text.like("%[GMAIL]%")
                    | Task.task_text.like("%[SIN]%")
                    | Task.task_text.like("%[PHONE]%")
                    | Task.task_text.like("%[SSN]%")
                )
            )
        ).scalar() or 0
        injection_blocked_tasks = (
            await self.session.execute(
                select(func.count(SecurityEvent.id)).where(
                    SecurityEvent.event_type == "injection_blocked"
                )
            )
        ).scalar() or 0

        success_rate = (completed / total * 100.0) if total else 0.0
        avg_steps_per_task = (total_steps / total) if total else 0.0

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "tool_usage": {row[0]: row[1] for row in tool_rows},
            "avg_execution_ms": float(avg_ms),
            "success_rate": round(success_rate, 2),
            "tool_success_rate": {
                row[0]: round(float(row[1] or 0.0) * 100.0, 2) for row in tool_success_rows
            },
            "observability": {
                "total_execution_steps": total_steps,
                "avg_steps_per_task": round(avg_steps_per_task, 2),
                "recent_failures": failed,
                "trace_step_types": {row[0]: row[1] for row in step_type_rows},
            },
            "security": {
                "pii_masked_tasks": pii_masked_tasks,
                "injection_blocked_tasks": injection_blocked_tasks,
                "validation_rules": [
                    "Task text length must be between 1 and 5000 characters",
                    "Prompt injection patterns are blocked before execution",
                    "PII masking is applied before task persistence",
                    "Tool-specific input validation runs before execution",
                ],
            },
        }


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, username: str, email: str, password_hash: str, role: str = "user") -> User:
        user = User(username=username, email=email, password_hash=password_hash, role=role)
        self.session.add(user)
        await self.session.flush()
        return user

    async def list_all(self) -> list[User]:
        result = await self.session.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    async def ensure_default_users(self) -> None:
        from passlib.context import CryptContext

        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

        defaults = [
            ("admin", "admin@bmo.local", "admin1234", "admin"),
            ("user", "user@bmo.local", "user1234", "user"),
            ("test1", "test1@bmo.local", "test1", "user"),
        ]
        for username, email, password, role in defaults:
            existing = await self.get_by_username(username)
            if not existing:
                await self.create(
                    username=username,
                    email=email,
                    password_hash=pwd.hash(password),
                    role=role,
                )

    async def ensure_default_user(self) -> User:
        await self.ensure_default_users()
        user = await self.get_by_username("admin")
        return user  # type: ignore[return-value]
