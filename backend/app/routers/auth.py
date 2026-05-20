from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_org_membership, get_current_user, require_roles
from app.models.membership import Membership, Role
from app.models.user import User
from app.schemas.auth import (
    AcceptInviteRequest,
    InviteRequest,
    RefreshRequest,
    SignInRequest,
    SignUpRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def sign_up(data: SignUpRequest, response: Response, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    result = await svc.sign_up(data)
    return result


@router.post("/signin", response_model=TokenResponse)
async def sign_in(data: SignInRequest, response: Response, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    result = await svc.sign_in(data.email, data.password)
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    return await svc.refresh(data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    await svc.logout(user.id)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.get("/organizations")
async def get_my_organizations(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    svc = AuthService(db)
    return await svc.get_user_organizations(user.id)


@router.get("/members")
async def get_org_members(
    membership: Membership = Depends(get_current_org_membership),
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    return await svc.get_org_members(membership.organization_id)


@router.post("/invite")
async def invite_member(
    data: InviteRequest,
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    return await svc.invite_member(
        org_id=membership.organization_id,
        email=data.email,
        role=Role(data.role),
        invited_by=membership.user_id,
    )


@router.post("/accept-invite", response_model=TokenResponse)
async def accept_invite(data: AcceptInviteRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    return await svc.accept_invite(data.token, data.password, data.full_name)
