class AgentError(Exception):
    """Base exception for agent layer."""


class EmptyTaskError(AgentError):
    """Raised when task text is empty or whitespace-only."""


class InvalidInputError(AgentError):
    """Raised when task input fails validation."""


class ToolExecutionError(AgentError):
    """Raised when a tool fails to execute."""


class ToolNotFoundError(AgentError):
    """Raised when no suitable tool is found."""


class TransientToolError(AgentError):
    """Raised when a tool fails temporarily and may succeed on retry."""


class DatabaseError(AgentError):
    """Raised when persistence fails."""
