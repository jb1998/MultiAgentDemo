"""Backward-compatible re-exports — prefer app.agents.routing."""

from app.agents.routing.models import RoutedTask
from app.agents.routing.smart_router import SmartRouter

__all__ = ["RoutedTask", "SmartRouter"]
