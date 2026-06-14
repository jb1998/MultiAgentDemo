"""Local development cost tracking for tool calls and hosting."""

# Per-tool invocation cost (USD) — cost per request to each tool
TOOL_COSTS: dict[str, float] = {
    "Calculator": 0.0012,
    "TextProcessor": 0.0008,
    "WeatherMock": 0.0025,
    "DateTimeTool": 0.0005,
    "JSONProcessorTool": 0.0010,
    "UnitConverterTool": 0.0009,
}

# Local hosting & infrastructure costs per request (USD)
INFRA_COSTS: dict[str, float] = {
    "SQLite Database (local)": 0.0002,
    "FastAPI Backend (local)": 0.0008,
    "React Frontend (Vite dev)": 0.0003,
}


def tool_call_cost(tool_name: str) -> float:
    return TOOL_COSTS.get(tool_name, 0.0010)


def infra_costs_for_request() -> dict[str, float]:
    return dict(INFRA_COSTS)


def total_infra_cost() -> float:
    return sum(INFRA_COSTS.values())
