from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import RegisterRequest, TokenResponse
from app.persistence.database import get_db
from app.persistence.repositories.task_repository import TaskRepository, UserRepository
from app.security.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    task_repo = TaskRepository(db)
    user = await repo.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        await task_repo.log_audit(
            action="login_failed",
            message=f"Failed login attempt for username: {form_data.username}",
            username=form_data.username,
            level="warning",
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(
        {"sub": user.username, "role": user.role, "user_id": user.id},
        expires_delta=timedelta(hours=1),
    )
    await task_repo.log_audit(
        action="login_success",
        message=f"User {user.username} logged in ({user.role})",
        user_id=user.id,
        username=user.username,
    )
    return TokenResponse(access_token=token, username=user.username, role=user.role)


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    task_repo = TaskRepository(db)
    if await repo.get_by_username(payload.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if await repo.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already exists")
    user = await repo.create(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    token = create_access_token(
        {"sub": user.username, "role": user.role, "user_id": user.id},
        expires_delta=timedelta(hours=1),
    )
    await task_repo.log_audit(
        action="user_registered",
        message=f"New user registered: {user.username}",
        user_id=user.id,
        username=user.username,
    )
    return TokenResponse(access_token=token, username=user.username, role=user.role)
