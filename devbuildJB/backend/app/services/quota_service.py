"""Per-user task quotas for rate-limited demo accounts."""

QUOTA_USERS: dict[str, int] = {
    "test1": 5,
}


def get_user_quota(username: str) -> int | None:
    return QUOTA_USERS.get(username)


def is_quota_exceeded(username: str, current_count: int) -> bool:
    quota = get_user_quota(username)
    if quota is None:
        return False
    return current_count >= quota
