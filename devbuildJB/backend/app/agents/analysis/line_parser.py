"""Parse multi-line task input."""

MIN_SMART_SUBTASKS = 2
MAX_SMART_SUBTASKS = 3


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def parse_lines(task_text: str) -> list[str]:
    return [line.strip() for line in normalize_newlines(task_text).split("\n") if line.strip()]


def count_lines(task_text: str) -> int:
    return len(parse_lines(task_text))


def should_use_smart_multi(task_text: str, mode: str) -> bool:
    if mode == "smart_multi":
        return True
    if mode == "single":
        return False
    return count_lines(task_text) >= MIN_SMART_SUBTASKS
