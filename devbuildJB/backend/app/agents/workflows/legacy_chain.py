"""Legacy chain: Calculator → TextProcessor for 'calculate X and convert to uppercase'."""

from app.agents.trace.models import ExecutionTrace
from app.agents.workflows.base import WorkflowResult
from app.agents.workflows.tool_steps import ToolStepRunner
from app.tools.tool_registry import tool_registry
from app.utils.exceptions import ToolNotFoundError

_ONES = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
_TEENS = [
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


class LegacyChainWorkflow:
    async def run(
        self,
        task_text: str,
        trace: ExecutionTrace,
        stream_delay: float = 0,
    ) -> WorkflowResult:
        calc_tool = tool_registry.get("Calculator")
        text_tool = tool_registry.get("TextProcessor")
        if not calc_tool or not text_tool:
            raise ToolNotFoundError("Required tools not available for multi-tool workflow")

        await trace.add_async(
            "workflow",
            "Detected multi-tool workflow — chaining Calculator → TextProcessor",
            stream_delay=stream_delay,
        )

        total_duration = 0
        tool_names: list[str] = []

        calc_confidence = calc_tool.confidence(task_text)
        await ToolStepRunner.record_selection(
            trace,
            calc_tool,
            calc_confidence,
            [(calc_tool.name, calc_confidence)],
            stream_delay,
            extra={"step": 1},
        )
        calc_output, calc_duration = await ToolStepRunner.execute(
            trace, calc_tool, task_text, stream_delay
        )
        total_duration += calc_duration
        tool_names.append(calc_tool.name)
        calc_result = calc_output.get("result", "")

        text_op = self._detect_text_op(task_text)
        try:
            num_val = int(float(calc_result))
            word_val = self._number_to_words(num_val)
        except (ValueError, TypeError):
            word_val = str(calc_result)

        text_task = f'Convert "{word_val}" to {text_op}'
        text_confidence = text_tool.confidence(text_task)
        await ToolStepRunner.record_selection(
            trace,
            text_tool,
            text_confidence,
            [(text_tool.name, text_confidence)],
            stream_delay,
            extra={"step": 2},
        )
        text_output, text_duration = await ToolStepRunner.execute(
            trace, text_tool, text_task, stream_delay
        )
        total_duration += text_duration
        tool_names.append(text_tool.name)
        text_result = text_output.get("result", "")

        final = f"The answer is {text_result}"
        return WorkflowResult(
            result=final,
            tool_names=" + ".join(tool_names),
            duration_ms=total_duration,
        )

    @staticmethod
    def _detect_text_op(task_text: str) -> str:
        t = task_text.lower()
        if "lowercase" in t or "lower case" in t:
            return "lowercase"
        if "reverse" in t:
            return "reverse"
        if "title" in t:
            return "title"
        return "uppercase"

    @staticmethod
    def _number_to_words(n: int) -> str:
        if n == 0:
            return "zero"
        if n < 0:
            return "negative " + LegacyChainWorkflow._number_to_words(-n)
        if n < 10:
            return _ONES[n]
        if n < 20:
            return _TEENS[n - 10]
        if n < 100:
            return (_TENS[n // 10] + (" " + _ONES[n % 10] if n % 10 else "")).strip()
        if n < 1000:
            return (
                _ONES[n // 100] + " hundred"
                + (" " + LegacyChainWorkflow._number_to_words(n % 100) if n % 100 else "")
            ).strip()
        return str(n)
