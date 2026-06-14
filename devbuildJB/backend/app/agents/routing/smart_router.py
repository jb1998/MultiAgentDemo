"""Map each sub-task line to the best tool."""

from app.agents.analysis.intent_detector import detect_primary_intent
from app.agents.analysis.line_parser import (
    MAX_SMART_SUBTASKS,
    MIN_SMART_SUBTASKS,
    parse_lines,
    should_use_smart_multi,
)
from app.agents.routing.models import RoutedTask
from app.agents.selection.tool_selector import ToolSelector
from app.utils.exceptions import ToolNotFoundError


class SmartRouter:
    @staticmethod
    def route_line(line: str, index: int) -> RoutedTask:
        tool, confidence, all_scores = ToolSelector.select(line)
        return RoutedTask(
            index=index,
            task_text=line,
            tool=tool,
            confidence=confidence,
            all_scores=all_scores,
            intent=detect_primary_intent(line),
        )

    @staticmethod
    def build_plan(task_text: str) -> list[RoutedTask]:
        lines = parse_lines(task_text)
        if len(lines) < MIN_SMART_SUBTASKS:
            raise ToolNotFoundError(
                f"Smart multi-tool mode requires {MIN_SMART_SUBTASKS}–{MAX_SMART_SUBTASKS} tasks (one per line)"
            )
        if len(lines) > MAX_SMART_SUBTASKS:
            raise ToolNotFoundError(
                f"Maximum {MAX_SMART_SUBTASKS} tasks allowed — received {len(lines)} lines"
            )
        return [SmartRouter.route_line(line, i + 1) for i, line in enumerate(lines)]

    @staticmethod
    def should_use_smart_multi(task_text: str, mode: str) -> bool:
        return should_use_smart_multi(task_text, mode)
