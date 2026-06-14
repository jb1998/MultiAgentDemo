from dataclasses import dataclass, field


@dataclass
class TaskAnalysis:
    task_text: str
    is_multi_tool: bool = False
    is_smart_multi: bool = False
    subtask_count: int = 0
    detected_intents: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "task_text": self.task_text,
            "is_multi_tool": self.is_multi_tool,
            "is_smart_multi": self.is_smart_multi,
            "subtask_count": self.subtask_count,
            "detected_intents": self.detected_intents,
            "summary": self.summary,
        }
