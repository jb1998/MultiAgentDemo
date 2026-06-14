import pytest

from app.tools.implementations import CalculatorTool, TextProcessorTool, WeatherMockTool
from app.utils.exceptions import TransientToolError


@pytest.mark.unit
class TestCalculatorTool:
    def test_basic_addition(self):
        tool = CalculatorTool()
        result = tool.execute("Calculate 3 + 5")
        assert result["result"] == "8"

    def test_division_by_zero(self):
        tool = CalculatorTool()
        with pytest.raises(ZeroDivisionError):
            tool.execute("5 / 0")

    def test_can_handle_math_expression(self):
        tool = CalculatorTool()
        assert tool.can_handle("10 * 2 + 3")


@pytest.mark.unit
class TestTextProcessorTool:
    def test_uppercase(self):
        tool = TextProcessorTool()
        result = tool.execute('Convert "hello" to uppercase')
        assert result["result"] == "HELLO"


@pytest.mark.unit
class TestWeatherMockTool:
    def test_transient_failure_on_first_attempt(self):
        from app.agents.retry.context import retry_attempt_ctx

        tool = WeatherMockTool()
        retry_attempt_ctx.set(1)
        with pytest.raises(TransientToolError):
            tool.execute("What is the weather in Tokyo?")

    def test_succeeds_on_retry_attempt(self):
        from app.agents.retry.context import retry_attempt_ctx

        tool = WeatherMockTool()
        retry_attempt_ctx.set(2)
        result = tool.execute("What is the weather in Tokyo?")
        assert "Tokyo" in result["result"]
