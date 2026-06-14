from abc import ABC, abstractmethod
from typing import Any

CONFIDENCE_THRESHOLD = 0.15


class Tool(ABC):
    """Abstract tool — extend this to add new capabilities."""

    name: str
    description: str
    keywords: list[str]
    version: str = "1.0.0"

    def confidence(self, task: str) -> float:
        """Return 0.0–1.0 confidence that this tool can handle the task."""
        text_lower = task.lower()
        matches = sum(1 for kw in self.keywords if kw.lower() in text_lower)
        if matches == 0:
            return 0.0
        return min(1.0, 0.55 + matches * 0.22)

    def can_handle(self, task: str) -> bool:
        return self.confidence(task) >= CONFIDENCE_THRESHOLD

    @abstractmethod
    def execute(self, task: str) -> dict[str, Any]:
        """Run the tool against the raw task string."""

    def get_metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "keywords": self.keywords,
            "version": self.version,
        }


# Backward-compatible alias
BaseTool = Tool
