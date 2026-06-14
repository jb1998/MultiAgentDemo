from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _user_rate_limit_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:24]
    return get_remote_address(request)


limiter = Limiter(key_func=_user_rate_limit_key, default_limits=["100/minute"])
