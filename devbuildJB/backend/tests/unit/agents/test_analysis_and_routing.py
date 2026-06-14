import pytest

from app.agents.analysis.line_parser import MAX_SMART_SUBTASKS, MIN_SMART_SUBTASKS, count_lines, parse_lines
from app.agents.analysis.task_analyzer import TaskAnalyzer
from app.agents.routing.smart_router import SmartRouter
from app.utils.exceptions import ToolNotFoundError


@pytest.mark.unit
def test_parse_lines_splits_on_newline():
    assert parse_lines("a\nb") == ["a", "b"]


@pytest.mark.unit
def test_line_limits():
    assert MIN_SMART_SUBTASKS == 2
    assert MAX_SMART_SUBTASKS == 3
    assert count_lines("a\nb\nc") == 3


@pytest.mark.unit
def test_smart_multi_analysis():
    analysis = TaskAnalyzer.analyze("1+1\nuppercase hello", mode="smart_multi")
    assert analysis.is_smart_multi
    assert analysis.subtask_count == 2


@pytest.mark.unit
def test_legacy_chain_detection():
    analysis = TaskAnalyzer.analyze("Calculate 10*2 and convert to uppercase", mode="single")
    assert analysis.is_multi_tool


@pytest.mark.unit
def test_smart_router_build_plan():
    plan = SmartRouter.build_plan("Calculate 1+1\nWeather in Tokyo")
    assert len(plan) == 2
    assert plan[0].tool.name == "Calculator"


@pytest.mark.unit
def test_smart_router_rejects_one_line():
    with pytest.raises(ToolNotFoundError):
        SmartRouter.build_plan("only one task")
