import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["AES_KEY"] = "01" * 32
os.environ["DEBUG"] = "false"
os.environ["JWT_EXPIRATION_MINUTES"] = "60"

import asyncio
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.rate_limiter import login_rate_limiter

settings.DATABASE_URL = "sqlite+aiosqlite:///./test.db"
settings.SECRET_KEY = "test-secret-key-for-testing-only"
settings.AES_KEY = "01" * 32
settings.DEBUG = False

TEST_DB = Path(__file__).parent / "test.db"


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()

    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest_asyncio.fixture
async def session(engine):
    TestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with TestSession() as s:
        yield s


@pytest_asyncio.fixture
async def client(engine):
    from app.db.database import get_db
    from main import app

    TestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with TestSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    login_rate_limiter._entries.clear()


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient):
    import uuid

    email = f"auth-{uuid.uuid4().hex[:12]}@example.com"
    password = "FixturePass1!"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture(autouse=True)
def _reset_rate_limiter():
    yield
    login_rate_limiter._entries.clear()
