import re
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

PII_PATTERNS = [
    (re.compile(r"\b[\w.-]+@[\w.-]+\.\w+\b"), "[EMAIL]"),
    (re.compile(r"@gmail\.com\b", re.I), "[GMAIL]"),
    (re.compile(r"\bSIN\b", re.I), "[SIN]"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
]

INJECTION_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"\bignore\b",
        r"\bdelete\b",
        r"ignore (all )?previous instructions",
        r"ignore previous instructions and",
        r"system prompt",
        r"<\s*script",
        r";\s*drop\s+table",
        r"union\s+select",
        r"you are now",
        r"disregard (all )?(prior|previous)",
    ]
]

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None


def mask_pii(text: str) -> str:
    masked = text
    for pattern, replacement in PII_PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked


def detect_injection(text: str) -> bool:
    return any(p.search(text) for p in INJECTION_PATTERNS)


def get_injection_reason(text: str) -> str | None:
    if detect_injection(text):
        return "Prompt injection detected. This request has been blocked."
    return None


def detect_pii(text: str) -> tuple[bool, list[str]]:
    types: list[str] = []
    for pattern, replacement in PII_PATTERNS:
        if pattern.search(text):
            label = replacement.strip("[]")
            if label not in types:
                types.append(label)
    return bool(types), types
