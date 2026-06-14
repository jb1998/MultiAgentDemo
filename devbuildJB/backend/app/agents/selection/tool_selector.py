"""Pick the best tool for a task using registry confidence scores."""

from app.observability.logger import get_logger
from app.tools.base_tool import CONFIDENCE_THRESHOLD, Tool
from app.tools.tool_registry import tool_registry
from app.utils.exceptions import ToolNotFoundError

logger = get_logger(__name__)


class ToolSelector:
    @staticmethod
    def select(task_text: str) -> tuple[Tool, float, list[tuple[str, float]]]:
        all_scores = tool_registry.score_all_tools(task_text)
        try:
            tool, confidence = tool_registry.select_tool(task_text)
        except ValueError:
            raise ToolNotFoundError("No suitable tool found") from None

        logger.info("Tool selected: %s (confidence=%.2f)", tool.name, confidence)
        return tool, confidence, all_scores

    @staticmethod
    def confidence_status(confidence: float) -> str:
        if confidence >= 0.8:
            return "HIGH CONFIDENCE"
        if confidence >= CONFIDENCE_THRESHOLD:
            return "PROCEEDING"
        return "LOW CONFIDENCE"
