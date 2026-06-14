"""Classify incoming tasks before tool selection."""

from app.agents.analysis.intent_detector import detect_intents
from app.agents.analysis.line_parser import count_lines, should_use_smart_multi
from app.agents.analysis.models import TaskAnalysis


class TaskAnalyzer:
    @staticmethod
    def analyze(task_text: str, mode: str = "auto") -> TaskAnalysis:
        intents = detect_intents(task_text)
        subtask_count = count_lines(task_text)
        is_smart = should_use_smart_multi(task_text, mode)
        is_multi = not is_smart and TaskAnalyzer._is_legacy_chain_task(task_text, intents)

        if is_smart:
            summary = (
                f"Smart multi-tool: {subtask_count} sub-tasks detected; "
                "routing each line to the best tool"
            )
        else:
            summary = (
                f"Detected intents: {', '.join(intents) or 'none'}; "
                f"multi-tool workflow: {'yes' if is_multi else 'no'}"
            )

        return TaskAnalysis(
            task_text=task_text,
            is_multi_tool=is_multi,
            is_smart_multi=is_smart,
            subtask_count=subtask_count,
            detected_intents=intents,
            summary=summary,
        )

    @staticmethod
    def _is_legacy_chain_task(task_text: str, intents: list[str]) -> bool:
        if " and " not in task_text.lower():
            return False
        return "calculation" in intents and "text_processing" in intents
