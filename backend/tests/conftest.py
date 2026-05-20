"""Shared test fixtures for the Wexa test suite.

Uses a separate test database (wexa_test) to avoid touching real data.
Tables are created once per session and dropped at the end.
"""
from __future__ import annotations

import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Base
from app.models.membership import Membership, Role
from app.models.organization import Organization
from app.models.user import User

# ---------------------------------------------------------------------------
# Test database URL — swap only the database name (last path segment)
# ---------------------------------------------------------------------------
_base = str(settings.database_url)
TEST_DB_URL = _base.rsplit("/", 1)[0] + "/wexa_test"


# ---------------------------------------------------------------------------
# Engine (session-scoped) — create tables once, drop at end
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


# ---------------------------------------------------------------------------
# Client — overrides get_db to use the test database
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client(engine):
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers — seed users/orgs directly in the test DB
# ---------------------------------------------------------------------------
async def seed_user_org(engine, role: Role = Role.OWNER):
    """Create a user + org + membership, return (headers, user, org)."""
    uid = uuid.uuid4().hex[:8]
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        user = User(
            email=f"{role.value}-{uid}@test.com",
            full_name=f"Test {role.value.title()}",
            hashed_password=hash_password("testpass123"),
        )
        org = Organization(name=f"Org-{uid}", slug=f"org-{uid}")
        session.add_all([user, org])
        await session.flush()

        session.add(Membership(user_id=user.id, organization_id=org.id, role=role))
        await session.commit()

        token = create_access_token({"sub": str(user.id)})
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Organization-ID": str(org.id),
        }
        return headers, user, org


@pytest_asyncio.fixture
async def owner_setup(engine):
    return await seed_user_org(engine, Role.OWNER)


@pytest_asyncio.fixture
async def viewer_setup(engine):
    return await seed_user_org(engine, Role.VIEWER)
