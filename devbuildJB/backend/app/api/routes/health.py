from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import HealthResponse
from app.persistence.database import get_db
from app.tools.tool_registry import tool_registry

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    tools = tool_registry.list_tools()
    tool_status = {tool.name: "healthy" for tool in tools}

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        backend="healthy",
        frontend="healthy",
        tools_available=len(tools),
        tool_status=tool_status,
        uptime_status="operational" if db_status == "healthy" else "degraded",
    )
