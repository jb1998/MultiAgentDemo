from contextvars import ContextVar

MAX_RETRIES = 3
RETRY_BACKOFF_SEC = 0.35

# Tools read this to simulate first-attempt transient failures (e.g. WeatherMock).
retry_attempt_ctx: ContextVar[int] = ContextVar("retry_attempt", default=1)
