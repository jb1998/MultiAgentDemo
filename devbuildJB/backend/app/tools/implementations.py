import ast
import json
import math
import operator
import re
from datetime import UTC, datetime
from typing import Any

from app.tools.base_tool import Tool
from app.utils.exceptions import TransientToolError

TEXT_OPS = {
    "uppercase": str.upper,
    "lowercase": str.lower,
    "title": str.title,
    "reverse": lambda s: s[::-1],
    "remove_spaces": lambda s: s.replace(" ", ""),
}


class TextProcessorTool(Tool):
    name = "TextProcessor"
    description = "Process text: uppercase, lowercase, title case, word count, reverse, remove spaces"
    keywords = [
        "uppercase", "lowercase", "title", "count words", "word count",
        "reverse", "remove spaces", "text", "string", "characters",
    ]

    def confidence(self, task: str) -> float:
        lowered = task.lower()
        if any(k in lowered for k in ("uppercase", "lowercase", "reverse", "word count", "remove space")):
            return 0.92
        return super().confidence(task)

    def execute(self, task: str) -> dict[str, Any]:
        text = self._extract_text(task)
        op = self._detect_operation(task)

        if op == "word_count":
            result = str(len(text.split()))
            meta = {"operation": op, "word_count": int(result)}
        elif op == "char_count":
            result = str(len(text))
            meta = {"operation": op, "char_count": int(result)}
        elif op in TEXT_OPS:
            result = TEXT_OPS[op](text)
            meta = {"operation": op}
        else:
            result = text.upper()
            meta = {"operation": "uppercase"}

        return {"result": result, "metadata": meta, "input_text": text}

    def _detect_operation(self, task_text: str) -> str:
        t = task_text.lower()
        if "uppercase" in t or "upper case" in t:
            return "uppercase"
        if "lowercase" in t or "lower case" in t:
            return "lowercase"
        if "title" in t:
            return "title"
        if "word count" in t or "count words" in t:
            return "word_count"
        if "character" in t and "count" in t:
            return "char_count"
        if "reverse" in t:
            return "reverse"
        if "remove space" in t:
            return "remove_spaces"
        return "uppercase"

    def _extract_text(self, task_text: str) -> str:
        quoted = re.findall(r'["\']([^"\']+)["\']', task_text)
        if quoted:
            return quoted[-1]

        lowered = task_text.lower()
        patterns = [
            r"(?:convert|change|make|turn)\s+(.+?)\s+(?:to|into)\s+(?:upper\s*case|uppercase|lower\s*case|lowercase|title(?:\s+case)?)",
            r"(?:reverse|count words in|count characters in|remove spaces from)\s+(.+)",
            r"(?:text|string)\s*:\s*(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, task_text, re.I)
            if match:
                return match.group(1).strip().strip('"').strip("'").strip("?.!")

        for prefix in ("text:", "string:"):
            if prefix in lowered:
                idx = lowered.index(prefix) + len(prefix)
                return task_text[idx:].strip().strip('"').strip("'").strip("?.!")

        parts = task_text.split(":", 1)
        if len(parts) > 1:
            return parts[1].strip().strip('"').strip("'").strip("?.!")
        return task_text.strip().strip("?.!")


class CalculatorTool(Tool):
    name = "Calculator"
    description = "Evaluate mathematical expressions safely"
    keywords = [
        "calculate", "compute", "math", "add", "subtract", "multiply",
        "divide", "sum", "sqrt", "+", "-", "*", "/", "expression",
    ]

    _OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
    }

    def confidence(self, task: str) -> float:
        lowered = task.lower()
        if re.search(r"\d+\s*[\+\-\*/\^%x]\s*\d+", lowered):
            return 0.95
        if any(word in lowered for word in ("calculate", "compute", "solve", "sqrt")):
            return 0.92
        return super().confidence(task)

    def execute(self, task: str) -> dict[str, Any]:
        expr = self._extract_expression(task)
        if not expr or not re.search(r"\d", expr):
            raise ValueError("Invalid math expression")

        sqrt_match = re.search(r"sqrt\s*\(\s*([\d.]+)\s*\)", expr, re.I)
        if sqrt_match:
            val = math.sqrt(float(sqrt_match.group(1)))
            return {"result": str(val), "expression": expr, "metadata": {"operation": "sqrt"}}

        tree = ast.parse(expr, mode="eval")
        value = self._safe_eval(tree.body)
        if value == int(value):
            value = int(value)
        return {"result": str(value), "expression": expr, "metadata": {"operation": "evaluate"}}

    def _extract_expression(self, task_text: str) -> str:
        lowered = task_text.lower()
        for word in ("calculate", "compute", "eval", "solve"):
            if word in lowered:
                idx = lowered.index(word) + len(word)
                expr = task_text[idx:].strip().strip("= ")
                if " and " in expr.lower():
                    expr = re.split(r"\s+and\s+", expr, maxsplit=1, flags=re.I)[0].strip()
                expr = re.sub(r"\s+", "", expr)
                return expr.replace("^", "**")

        match = re.search(
            r"(\d+(?:\.\d+)?(?:\s*[\+\-\*/\^%]\s*\d+(?:\.\d+)?)+)",
            task_text,
        )
        if match:
            return re.sub(r"\s+", "", match.group(1)).replace("^", "**")

        compact = task_text.replace("^", "**").replace(" ", "")
        match = re.search(r"[\d+\-*/().%\^]+", compact)
        if match:
            return match.group()
        return compact.strip()

    def _safe_eval(self, node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            if isinstance(node.op, ast.Div) and right == 0:
                raise ZeroDivisionError("Division by zero")
            op = self._OPS.get(type(node.op))
            if op is None:
                raise ValueError("Unsupported operator")
            return op(left, right)
        if isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            op = self._OPS.get(type(node.op))
            if op is None:
                raise ValueError("Unsupported unary operator")
            return op(operand)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "sqrt" and len(node.args) == 1:
                return math.sqrt(self._safe_eval(node.args[0]))
            if node.func.id == "abs" and len(node.args) == 1:
                return abs(self._safe_eval(node.args[0]))
        raise ValueError("Invalid expression")


class WeatherMockTool(Tool):
    name = "WeatherMock"
    description = "Get mock weather data for a city"
    keywords = ["weather", "temperature", "forecast", "humidity", "wind", "climate"]

    MOCK_DATA = {
        "new york": {"temp": 22, "condition": "Partly Cloudy", "humidity": 65, "wind": "12 km/h"},
        "london": {"temp": 15, "condition": "Rainy", "humidity": 80, "wind": "18 km/h"},
        "tokyo": {"temp": 28, "condition": "Sunny", "humidity": 55, "wind": "8 km/h"},
        "paris": {"temp": 18, "condition": "Overcast", "humidity": 70, "wind": "10 km/h"},
        "sydney": {"temp": 25, "condition": "Clear", "humidity": 60, "wind": "15 km/h"},
        "default": {"temp": 20, "condition": "Mild", "humidity": 50, "wind": "10 km/h"},
    }

    def confidence(self, task: str) -> float:
        lowered = task.lower()
        if "weather" in lowered or "forecast" in lowered:
            return 0.92
        return super().confidence(task)

    def execute(self, task: str) -> dict[str, Any]:
        from app.agents.retry.context import retry_attempt_ctx

        if retry_attempt_ctx.get() == 1 and "weather" in task.lower():
            raise TransientToolError("Weather service temporarily unavailable")

        city = self._extract_city(task)
        data = self.MOCK_DATA.get(city, self.MOCK_DATA["default"])
        result = (
            f"Weather in {city.title()}: {data['temp']}°C, {data['condition']}. "
            f"Humidity: {data['humidity']}%, Wind: {data['wind']}"
        )
        return {"result": result, "city": city, "metadata": data}

    def _extract_city(self, task_text: str) -> str:
        patterns = [
            r"weather (?:in|for|at) ([a-zA-Z\s]+)",
            r"temperature (?:in|for|at) ([a-zA-Z\s]+)",
            r"forecast (?:for|in) ([a-zA-Z\s]+)",
        ]
        for pat in patterns:
            m = re.search(pat, task_text, re.I)
            if m:
                return m.group(1).strip().lower()
        words = task_text.split()
        for i, w in enumerate(words):
            if w.lower() in ("in", "for", "at") and i + 1 < len(words):
                return " ".join(words[i + 1 :]).strip("?.!").lower()
        return "default"


class DateTimeTool(Tool):
    name = "DateTimeTool"
    description = "Get current date/time, format dates, and convert USD to CAD using a mock exchange rate"
    keywords = [
        "time", "date", "datetime", "current time", "current date",
        "format date", "today", "usd to cad", "currency", "exchange rate",
    ]

    USD_TO_CAD_RATE = 1.37

    def confidence(self, task: str) -> float:
        lowered = task.lower()
        if "current time" in lowered or "current date" in lowered:
            return 0.95
        if "usd" in lowered and "cad" in lowered:
            return 0.93
        return super().confidence(task)

    def execute(self, task: str) -> dict[str, Any]:
        lowered = task.lower()
        now = datetime.now(UTC)

        if "usd" in lowered and "cad" in lowered:
            amount_match = re.search(r"(\d+(?:\.\d+)?)\s*usd", lowered)
            amount = float(amount_match.group(1)) if amount_match else 1.0
            converted = round(amount * self.USD_TO_CAD_RATE, 2)
            return {
                "result": f"{amount:.2f} USD = {converted:.2f} CAD",
                "metadata": {
                    "operation": "usd_to_cad",
                    "rate": self.USD_TO_CAD_RATE,
                    "amount_usd": amount,
                    "amount_cad": converted,
                },
            }

        if "format" in lowered and "date" in lowered:
            return {
                "result": now.strftime("%A, %B %d, %Y %H:%M:%S UTC"),
                "metadata": {"operation": "format_datetime", "timezone": "UTC"},
            }

        if "time" in lowered:
            return {
                "result": now.strftime("%H:%M:%S UTC"),
                "metadata": {"operation": "current_time", "timezone": "UTC"},
            }

        return {
            "result": now.strftime("%Y-%m-%d"),
            "metadata": {"operation": "current_date", "timezone": "UTC"},
        }


class JSONProcessorTool(Tool):
    name = "JSONProcessorTool"
    description = "Parse, validate, and pretty-format JSON payloads"
    keywords = [
        "json", "parse json", "validate json", "format json",
        "pretty print json", "minify json", "serialize",
    ]

    def confidence(self, task: str) -> float:
        if re.search(r"(\{.*\}|\[.*\])", task, re.S):
            return max(0.9, super().confidence(task))
        return super().confidence(task)

    def execute(self, task: str) -> dict[str, Any]:
        payload = self._extract_json(task)
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc.msg}") from exc

        lowered = task.lower()
        if "minify" in lowered:
            result = json.dumps(parsed, separators=(",", ":"))
            operation = "minify"
        else:
            result = json.dumps(parsed, indent=2, sort_keys=True)
            operation = "format"

        return {
            "result": result,
            "metadata": {
                "operation": operation,
                "valid": True,
                "type": type(parsed).__name__,
            },
        }

    def _extract_json(self, task_text: str) -> str:
        match = re.search(r"(\{.*\}|\[.*\])", task_text, re.S)
        if match:
            return match.group(1)
        return task_text.strip()


class UnitConverterTool(Tool):
    name = "UnitConverterTool"
    description = "Convert length, weight, and temperature units"
    keywords = [
        "convert", "unit", "meters", "kilometers", "miles", "kg", "lbs",
        "celsius", "fahrenheit", "temperature conversion", "length conversion",
    ]

    def confidence(self, task: str) -> float:
        lowered = task.lower()
        if re.search(r"\d+\s*(km|m|mi|miles?|kg|lb|celsius|fahrenheit)", lowered):
            return max(0.9, super().confidence(task))
        return super().confidence(task)

    def execute(self, task: str) -> dict[str, Any]:
        task_text = task.lower()

        temp_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(c|celsius|f|fahrenheit)\s+(?:to)\s+(c|celsius|f|fahrenheit)",
            task_text,
        )
        if temp_match:
            value = float(temp_match.group(1))
            from_unit = temp_match.group(2)[0]
            to_unit = temp_match.group(3)[0]
            if from_unit == to_unit:
                converted = value
            elif from_unit == "c":
                converted = (value * 9 / 5) + 32
            else:
                converted = (value - 32) * 5 / 9
            return {
                "result": f"{value:g}°{from_unit.upper()} = {converted:.2f}°{to_unit.upper()}",
                "metadata": {"operation": "temperature", "from_unit": from_unit, "to_unit": to_unit},
            }

        length_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(km|kilometers?|m|meters?|mi|miles?)\s+(?:to)\s+(km|kilometers?|m|meters?|mi|miles?)",
            task_text,
        )
        if length_match:
            value = float(length_match.group(1))
            from_unit = length_match.group(2)
            to_unit = length_match.group(3)
            to_meters = {
                "m": 1, "meter": 1, "meters": 1,
                "km": 1000, "kilometer": 1000, "kilometers": 1000,
                "mi": 1609.34, "mile": 1609.34, "miles": 1609.34,
            }
            meters = value * to_meters[from_unit]
            converted = meters / to_meters[to_unit]
            return {
                "result": f"{value:g} {from_unit} = {converted:.2f} {to_unit}",
                "metadata": {"operation": "length", "from_unit": from_unit, "to_unit": to_unit},
            }

        weight_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(kg|kilograms?|lb|lbs|pounds?)\s+(?:to)\s+(kg|kilograms?|lb|lbs|pounds?)",
            task_text,
        )
        if weight_match:
            value = float(weight_match.group(1))
            from_unit = weight_match.group(2)
            to_unit = weight_match.group(3)
            to_kg = {
                "kg": 1, "kilogram": 1, "kilograms": 1,
                "lb": 0.453592, "lbs": 0.453592, "pound": 0.453592, "pounds": 0.453592,
            }
            kilograms = value * to_kg[from_unit]
            converted = kilograms / to_kg[to_unit]
            return {
                "result": f"{value:g} {from_unit} = {converted:.2f} {to_unit}",
                "metadata": {"operation": "weight", "from_unit": from_unit, "to_unit": to_unit},
            }

        raise ValueError("Unsupported conversion request")
