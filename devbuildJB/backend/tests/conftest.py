"""
Pytest configuration — set test env before app imports.
"""

import os
import tempfile

# Isolated SQLite file (shared across connections in one test run)
_TEST_DB = os.path.join(tempfile.gettempdir(), f"omb_pytest_{os.getpid()}.db")
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-pytest-only"

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.rate_limit import limiter
from app.main import app
from app.persistence.database import async_session, init_db
from app.persistence.repositories.task_repository import UserRepository


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    await init_db()
    async with async_session() as session:
        repo = UserRepository(session)
        await repo.ensure_default_users()
        await session.commit()
    yield
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)


@pytest.fixture(autouse=True)
def disable_rate_limits():
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin1234"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def user_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "user", "password": "user1234"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest_asyncio.fixture
async def user_headers(user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}
