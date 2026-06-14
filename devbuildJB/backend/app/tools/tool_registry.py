from app.tools.base_tool import CONFIDENCE_THRESHOLD, Tool
from app.tools.implementations import (
    CalculatorTool,
    DateTimeTool,
    JSONProcessorTool,
    TextProcessorTool,
    UnitConverterTool,
    WeatherMockTool,
)


def _is_math_task(task_text: str) -> bool:
    return any(c.isdigit() for c in task_text) and any(
        op in task_text for op in ["+", "-", "*", "/", "calculate", "compute"]
    )


class ToolRegistry:
    """Central registry — register new tools here to extend the agent."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self.register(TextProcessorTool())
        self.register(CalculatorTool())
        self.register(WeatherMockTool())
        self.register(DateTimeTool())
        self.register(JSONProcessorTool())
        self.register(UnitConverterTool())

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def score_all_tools(self, task_text: str) -> list[tuple[str, float]]:
        scores = [(tool.name, round(tool.confidence(task_text), 4)) for tool in self._tools.values()]
        return sorted(scores, key=lambda x: x[1], reverse=True)

    def find_capable_tools(self, task_text: str) -> list[tuple[Tool, float]]:
        scored = [(tool, tool.confidence(task_text)) for tool in self._tools.values()]
        return sorted([(t, s) for t, s in scored if s > 0], key=lambda x: x[1], reverse=True)

    def select_tool(self, task_text: str) -> tuple[Tool, float]:
        capable = self.find_capable_tools(task_text)
        if not capable:
            if _is_math_task(task_text):
                return self._tools["Calculator"], 0.85
            raise ValueError("No suitable tool found")

        best_tool, best_score = capable[0]
        if best_score < CONFIDENCE_THRESHOLD:
            if _is_math_task(task_text):
                return self._tools["Calculator"], 0.85
            raise ValueError("No suitable tool found")
        return best_tool, best_score


tool_registry = ToolRegistry()
