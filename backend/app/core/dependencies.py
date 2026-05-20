from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token, hash_api_key
from app.models.api_key import ApiKey
from app.models.membership import Membership, Role
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Missing authentication token")
    try:
        payload = decode_token(credentials.credentials)
    except ValueError:
        raise UnauthorizedError("Invalid or expired token")
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError()
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id), User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedError("User not found or inactive")
    return user


async def get_current_org_membership(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Membership:
    org_id_str = request.headers.get("X-Organization-ID")
    if not org_id_str:
        raise HTTPException(status_code=400, detail="X-Organization-ID header is required")
    try:
        org_id = uuid.UUID(org_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid organization ID")
    result = await db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.organization_id == org_id,
            Membership.is_active.is_(True),
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise ForbiddenError("You are not a member of this organization")
    return membership


def require_roles(*allowed: Role):
    async def checker(membership: Membership = Depends(get_current_org_membership)) -> Membership:
        if membership.role not in allowed:
            raise ForbiddenError(f"Requires one of: {[r.value for r in allowed]}")
        return membership
    return checker


async def get_api_key_org(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    """Authenticate via X-API-Key header — used for ingestion endpoints."""
    raw_key = request.headers.get("X-API-Key")
    if not raw_key:
        raise UnauthorizedError("X-API-Key header required")
    key_hash = hash_api_key(raw_key)
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise UnauthorizedError("Invalid API key")
    return api_key
