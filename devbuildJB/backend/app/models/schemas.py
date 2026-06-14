from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class TaskCreate(BaseModel):
    task_text: str = Field(..., min_length=1, max_length=5000)
    mode: Literal["auto", "single", "smart_multi"] = "auto"

    @field_validator("task_text")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Task text cannot be empty")
        return stripped


class ExecutionStepResponse(BaseModel):
    id: int
    step_number: int
    step_type: str
    description: str
    tool_name: str | None = None
    input_data: str | None = None
    output_data: str | None = None
    timestamp: datetime
    duration_ms: int | None = None

    model_config = {"from_attributes": True}


class TaskResponse(BaseModel):
    id: int
    task_text: str
    status: str
    result: str | None = None
    trace_id: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    execution_steps: list[ExecutionStepResponse] = []

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
    page: int
    page_size: int


class ToolMetadata(BaseModel):
    name: str
    description: str
    keywords: list[str]
    version: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SecuritySummary(BaseModel):
    pii_masked_tasks: int
    injection_blocked_tasks: int
    validation_rules: list[str]


class ObservabilitySummary(BaseModel):
    total_execution_steps: int
    avg_steps_per_task: float
    recent_failures: int
    trace_step_types: dict[str, int]


class MetricsResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    tool_usage: dict[str, int]
    avg_execution_ms: float
    success_rate: float
    tool_success_rate: dict[str, float]
    observability: ObservabilitySummary
    security: SecuritySummary


class HealthResponse(BaseModel):
    status: str
    database: str
    backend: str = "healthy"
    frontend: str = "healthy"
    tools_available: int
    tool_status: dict[str, str] = {}
    uptime_status: str = "operational"


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None = None
    username: str | None = None
    action: str
    message: str
    level: str
    metadata_json: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CostRecordResponse(BaseModel):
    id: int
    task_id: int | None = None
    tool_name: str | None = None
    service_name: str
    cost_usd: float
    duration_ms: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CostSummaryResponse(BaseModel):
    total_cost_usd: float
    tool_costs: dict[str, dict[str, float | int]]
    service_costs: dict[str, dict[str, float | int]]
    recent_records: list[CostRecordResponse]


class MessageResponse(BaseModel):
    message: str
    data: Any | None = None
