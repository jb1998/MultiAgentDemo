"""Shared intent detection for analysis and routing."""

import re


def detect_intents(text: str) -> list[str]:
    lowered = text.lower()
    intents: list[str] = []

    if re.search(r"\d+\s*[\+\-\*/\^%x]\s*\d+", lowered) or any(
        k in lowered for k in ("calculate", "compute", "sqrt")
    ):
        intents.append("calculation")
    if any(k in lowered for k in ("uppercase", "lowercase", "reverse", "word count", "remove space")):
        intents.append("text_processing")
    if "weather" in lowered or "forecast" in lowered:
        intents.append("weather")
    if any(k in lowered for k in ("time", "date", "today")):
        intents.append("datetime")
    if "json" in lowered or re.search(r"(\{.*\}|\[.*\])", text, re.S):
        intents.append("json")
    if "convert" in lowered and re.search(r"\d+\s*(km|m|mi|kg|lb|c|f)", lowered):
        intents.append("unit_conversion")

    return intents


def detect_primary_intent(line: str) -> str:
    intents = detect_intents(line)
    return intents[0] if intents else "general"
