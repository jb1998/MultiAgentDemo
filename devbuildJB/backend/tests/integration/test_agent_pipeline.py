import pytest

from app.agents.runner.task_runner import TaskRunner
from app.persistence.database import async_session
from app.persistence.repositories.task_repository import TaskRepository, UserRepository
from app.orchestration.controller import AgentController


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_controller_persists_task():
    async with async_session() as session:
        user_repo = UserRepository(session)
        admin = await user_repo.get_by_username("admin")
        assert admin is not None

        task_repo = TaskRepository(session)
        task = await task_repo.create(user_id=admin.id, task_text="Calculate 2 + 2")
        await session.commit()

        controller = AgentController(session)
        await controller.process_task(task.id, username="admin")

        refreshed = await task_repo.get_by_id(task.id)
        await session.refresh(refreshed, attribute_names=["execution_steps"])
        assert refreshed is not None
        assert refreshed.status == "completed"
        assert refreshed.result == "4"
        assert len(refreshed.execution_steps) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_task_runner_smart_multi_integration():
    text = """Calculate 10 + 5
Convert "hi" to uppercase"""
    runner = TaskRunner()
    result = await runner.run(text, mode="smart_multi", stream_delay=0)
    assert result.success
    assert "Calculator" in result.tool_name
    assert "TextProcessor" in result.tool_name
    assert "15" in result.result
    assert "HI" in result.result.upper()
