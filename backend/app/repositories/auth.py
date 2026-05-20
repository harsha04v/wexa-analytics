from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership, Role
from app.models.refresh_token import RefreshToken
from app.models.invitation import Invitation


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, *, email: str, hashed_password: str, full_name: str) -> User:
        user = User(email=email, hashed_password=hashed_password, full_name=full_name)
        self.db.add(user)
        await self.db.flush()
        return user


class OrganizationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, org_id: uuid.UUID) -> Organization | None:
        result = await self.db.execute(
            select(Organization).where(Organization.id == org_id, Organization.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self.db.execute(select(Organization).where(Organization.slug == slug))
        return result.scalar_one_or_none()

    async def create(self, *, name: str, slug: str) -> Organization:
        org = Organization(name=name, slug=slug)
        self.db.add(org)
        await self.db.flush()
        return org

    async def update(self, org: Organization, **kwargs) -> Organization:
        for k, v in kwargs.items():
            setattr(org, k, v)
        await self.db.flush()
        return org


class MembershipRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, user_id: uuid.UUID, org_id: uuid.UUID) -> Membership | None:
        result = await self.db.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.organization_id == org_id,
                Membership.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(self, org_id: uuid.UUID) -> list[Membership]:
        result = await self.db.execute(
            select(Membership).where(
                Membership.organization_id == org_id,
                Membership.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def list_by_user(self, user_id: uuid.UUID) -> list[Membership]:
        result = await self.db.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def create(self, *, user_id: uuid.UUID, org_id: uuid.UUID, role: Role) -> Membership:
        m = Membership(user_id=user_id, organization_id=org_id, role=role)
        self.db.add(m)
        await self.db.flush()
        return m

    async def remove(self, membership: Membership) -> None:
        membership.is_active = False
        await self.db.flush()


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshToken:
        rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(rt)
        await self.db.flush()
        return rt

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )


class InvitationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, *, email: str, org_id: uuid.UUID, role: Role, invited_by: uuid.UUID, token: str, expires_at: datetime
    ) -> Invitation:
        inv = Invitation(
            email=email, organization_id=org_id, role=role, invited_by=invited_by, token=token, expires_at=expires_at
        )
        self.db.add(inv)
        await self.db.flush()
        return inv

    async def get_by_token(self, token: str) -> Invitation | None:
        result = await self.db.execute(
            select(Invitation).where(
                Invitation.token == token,
                Invitation.accepted_at.is_(None),
                Invitation.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def accept(self, invitation: Invitation) -> None:
        invitation.accepted_at = datetime.now(timezone.utc)
        await self.db.flush()
