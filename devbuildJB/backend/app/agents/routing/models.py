from dataclasses import dataclass

from app.tools.base_tool import Tool


@dataclass
class RoutedTask:
    index: int
    task_text: str
    tool: Tool
    confidence: float
    all_scores: list[tuple[str, float]]
    intent: str

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "task_text": self.task_text,
            "tool": self.tool.name,
            "confidence": round(self.confidence, 4),
            "intent": self.intent,
            "all_scores": [{"tool": n, "score": s} for n, s in self.all_scores],
        }
