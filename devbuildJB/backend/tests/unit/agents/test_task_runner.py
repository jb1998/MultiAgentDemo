import pytest

from app.agents.runner.task_runner import TaskRunner


@pytest.mark.unit
@pytest.mark.asyncio
async def test_division_by_zero_records_error_step():
    runner = TaskRunner()
    result = await runner.run("5 / 0", mode="single", stream_delay=0)
    assert not result.success
    assert result.error == "Division by zero"
    step_types = {s.step_type for s in result.trace.steps}
    assert "error" in step_types
    assert any(s.action == "Tool execution failed" for s in result.trace.steps)
