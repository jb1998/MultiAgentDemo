import pytest

from app.agents.trace.models import ExecutionTrace
from app.agents.workflows.dispatcher import WorkflowDispatcher


@pytest.mark.unit
def test_intent_detector_calculation():
    from app.agents.analysis.intent_detector import detect_intents

    assert "calculation" in detect_intents("Calculate 15 + 20")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_workflow_dispatcher_single_tool():
    trace = ExecutionTrace()
    result = await WorkflowDispatcher.dispatch("Calculate 3 + 5", "single", trace, 0)
    assert result.result == "8"
    assert result.tool_names == "Calculator"
