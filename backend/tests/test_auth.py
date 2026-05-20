"""Tests for authentication & multi-tenancy endpoints."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_signup_success(client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    res = await client.post("/api/v1/auth/signup", json={
        "email": f"signup-{uid}@example.com",
        "password": "securepass123",
        "full_name": "New User",
        "organization_name": "New Corp",
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == f"signup-{uid}@example.com"


async def test_signin_success(client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    email = f"signin-{uid}@example.com"
    # Create user first
    await client.post("/api/v1/auth/signup", json={
        "email": email,
        "password": "securepass123",
        "full_name": "Login User",
        "organization_name": "Login Org",
    })
    res = await client.post("/api/v1/auth/signin", json={
        "email": email,
        "password": "securepass123",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


async def test_me_without_token(client: AsyncClient):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401


async def test_me_with_token(client: AsyncClient, owner_setup):
    headers, user, _ = owner_setup
    res = await client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == user.email


async def test_viewer_cannot_invite(client: AsyncClient, viewer_setup):
    headers, _, _ = viewer_setup
    res = await client.post("/api/v1/auth/invite", headers=headers, json={
        "email": "blocked@example.com",
        "role": "viewer",
    })
    assert res.status_code == 403
