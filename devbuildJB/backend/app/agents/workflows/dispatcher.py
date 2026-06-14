"""Select and run the appropriate workflow for a task."""

from app.agents.analysis.task_analyzer import TaskAnalyzer
from app.agents.routing.smart_router import SmartRouter
from app.agents.trace.models import ExecutionTrace
from app.agents.workflows.base import WorkflowResult
from app.agents.workflows.legacy_chain import LegacyChainWorkflow
from app.agents.workflows.single_tool import SingleToolWorkflow
from app.agents.workflows.smart_multi import SmartMultiWorkflow


class WorkflowDispatcher:
    _smart_multi = SmartMultiWorkflow()
    _legacy_chain = LegacyChainWorkflow()
    _single_tool = SingleToolWorkflow()

    @classmethod
    async def dispatch(
        cls,
        task_text: str,
        mode: str,
        trace: ExecutionTrace,
        stream_delay: float = 0,
    ) -> WorkflowResult:
        if SmartRouter.should_use_smart_multi(task_text, mode):
            return await cls._smart_multi.run(task_text, trace, stream_delay)

        analysis = TaskAnalyzer.analyze(task_text, mode=mode)
        if analysis.is_multi_tool:
            return await cls._legacy_chain.run(task_text, trace, stream_delay)

        return await cls._single_tool.run(task_text, trace, stream_delay)
