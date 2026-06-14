"""
Modular agent layer.

Layers (each is a separate package — add features by extending, not editing runners):

  trace      → step recording and streaming callbacks
  analysis   → task classification and line parsing
  selection  → tool confidence scoring and picking
  routing    → multi-line smart routing plans
  workflows  → execution strategies (single, chain, smart multi)
  retry      → transient failure handling
  runner     → thin pipeline orchestration
"""

from app.agents.analysis import TaskAnalysis, TaskAnalyzer
from app.agents.runner import RunResult, STREAM_STEP_DELAY_SEC, TaskRunner
from app.agents.routing import RoutedTask, SmartRouter
from app.agents.selection import ToolSelector
from app.agents.trace import ExecutionTrace, StepCallback, TraceStep
from app.agents.workflows import WorkflowDispatcher

__all__ = [
    "TaskRunner",
    "RunResult",
    "STREAM_STEP_DELAY_SEC",
    "ExecutionTrace",
    "TraceStep",
    "StepCallback",
    "TaskAnalyzer",
    "TaskAnalysis",
    "ToolSelector",
    "SmartRouter",
    "RoutedTask",
    "WorkflowDispatcher",
]
