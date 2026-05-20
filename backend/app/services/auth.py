from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_invite_token,
    hash_password,
    verify_password,
)
from app.models.membership import Role
from app.repositories.auth import (
    InvitationRepository,
    MembershipRepository,
    OrganizationRepository,
    RefreshTokenRepository,
    UserRepository,
)
from app.schemas.auth import SignUpRequest, TokenResponse, UserResponse


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.orgs = OrganizationRepository(db)
        self.memberships = MembershipRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.invitations = InvitationRepository(db)

    async def sign_up(self, data: SignUpRequest) -> TokenResponse:
        existing = await self.users.get_by_email(data.email)
        if existing:
            raise ConflictError("Email already registered")

        user = await self.users.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )

        slug = re.sub(r"[^a-z0-9]+", "-", data.organization_name.lower()).strip("-")
        existing_org = await self.orgs.get_by_slug(slug)
        if existing_org:
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"

        org = await self.orgs.create(name=data.organization_name, slug=slug)
        await self.memberships.create(user_id=user.id, org_id=org.id, role=Role.OWNER)

        return await self._create_tokens(user)

    async def sign_in(self, email: str, password: str) -> TokenResponse:
        user = await self.users.get_by_email(email)
        if not user or not user.is_active:
            raise UnauthorizedError("Invalid email or password")
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        return await self._create_tokens(user)

    async def refresh(self, refresh_token_str: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token_str)
        except ValueError:
            raise UnauthorizedError("Invalid refresh token")
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()
        stored = await self.refresh_tokens.get_by_hash(token_hash)
        if not stored:
            raise UnauthorizedError("Refresh token revoked or expired")

        await self.refresh_tokens.revoke(stored)

        user = await self.users.get_by_id(uuid.UUID(payload["sub"]))
        if not user:
            raise UnauthorizedError("User not found")

        return await self._create_tokens(user)

    async def logout(self, user_id: uuid.UUID) -> None:
        await self.refresh_tokens.revoke_all_for_user(user_id)

    async def invite_member(
        self, *, org_id: uuid.UUID, email: str, role: Role, invited_by: uuid.UUID
    ) -> dict:
        token = generate_invite_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        invitation = await self.invitations.create(
            email=email, org_id=org_id, role=role, invited_by=invited_by, token=token, expires_at=expires_at
        )
        return {
            "id": invitation.id,
            "email": invitation.email,
            "role": invitation.role.value,
            "token": invitation.token,
            "expires_at": invitation.expires_at,
            "created_at": invitation.created_at,
        }

    async def accept_invite(self, token: str, password: str, full_name: str) -> TokenResponse:
        invitation = await self.invitations.get_by_token(token)
        if not invitation:
            raise NotFoundError("Invitation")

        existing = await self.users.get_by_email(invitation.email)
        if existing:
            # Already has account — just add membership
            user = existing
        else:
            user = await self.users.create(
                email=invitation.email,
                hashed_password=hash_password(password),
                full_name=full_name,
            )

        await self.memberships.create(
            user_id=user.id, org_id=invitation.organization_id, role=invitation.role
        )
        await self.invitations.accept(invitation)

        return await self._create_tokens(user)

    async def get_user_organizations(self, user_id: uuid.UUID) -> list[dict]:
        memberships = await self.memberships.list_by_user(user_id)
        result = []
        for m in memberships:
            org = await self.orgs.get_by_id(m.organization_id)
            if org:
                result.append({
                    "id": org.id,
                    "name": org.name,
                    "slug": org.slug,
                    "role": m.role.value,
                    "created_at": org.created_at,
                })
        return result

    async def get_org_members(self, org_id: uuid.UUID) -> list[dict]:
        memberships = await self.memberships.list_by_org(org_id)
        result = []
        for m in memberships:
            user = await self.users.get_by_id(m.user_id)
            if user:
                result.append({
                    "id": m.id,
                    "user_id": user.id,
                    "organization_id": m.organization_id,
                    "role": m.role.value,
                    "is_active": m.is_active,
                    "user_email": user.email,
                    "user_name": user.full_name,
                    "created_at": m.created_at,
                })
        return result

    async def _create_tokens(self, user) -> TokenResponse:
        access = create_access_token({"sub": str(user.id)})
        refresh = create_refresh_token({"sub": str(user.id)})

        token_hash = hashlib.sha256(refresh.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await self.refresh_tokens.create(user_id=user.id, token_hash=token_hash, expires_at=expires_at)

        return TokenResponse(
            access_token=access,
            user=UserResponse.model_validate(user),
        )
