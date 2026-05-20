from __future__ import annotations

import secrets
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dashboard import Dashboard, Widget, WidgetType


class DashboardRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, *, org_id: uuid.UUID, name: str, description: str | None, created_by: uuid.UUID
    ) -> Dashboard:
        d = Dashboard(organization_id=org_id, name=name, description=description, created_by=created_by)
        self.db.add(d)
        await self.db.flush()
        await self.db.refresh(d, attribute_names=["widgets"])
        return d

    async def get(self, dashboard_id: uuid.UUID, org_id: uuid.UUID) -> Dashboard | None:
        result = await self.db.execute(
            select(Dashboard)
            .options(selectinload(Dashboard.widgets))
            .where(
                Dashboard.id == dashboard_id,
                Dashboard.organization_id == org_id,
                Dashboard.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_share_token(self, token: str) -> Dashboard | None:
        result = await self.db.execute(
            select(Dashboard)
            .options(selectinload(Dashboard.widgets))
            .where(
                Dashboard.share_token == token,
                Dashboard.is_public.is_(True),
                Dashboard.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(self, org_id: uuid.UUID) -> list[Dashboard]:
        result = await self.db.execute(
            select(Dashboard)
            .options(selectinload(Dashboard.widgets))
            .where(Dashboard.organization_id == org_id, Dashboard.is_active.is_(True))
            .order_by(Dashboard.created_at.desc())
        )
        return list(result.unique().scalars().all())

    async def update(self, dashboard: Dashboard, **kwargs) -> Dashboard:
        for k, v in kwargs.items():
            setattr(dashboard, k, v)
        await self.db.flush()
        return dashboard

    async def delete(self, dashboard: Dashboard) -> None:
        dashboard.is_active = False
        await self.db.flush()

    async def toggle_public(self, dashboard: Dashboard) -> Dashboard:
        dashboard.is_public = not dashboard.is_public
        if dashboard.is_public and not dashboard.share_token:
            dashboard.share_token = secrets.token_urlsafe(16)
        elif not dashboard.is_public:
            dashboard.share_token = None
        await self.db.flush()
        await self.db.refresh(dashboard)
        await self.db.refresh(dashboard, attribute_names=["widgets"])
        return dashboard


class WidgetRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, *, dashboard_id: uuid.UUID, name: str, widget_type: WidgetType, config: dict, position: dict
    ) -> Widget:
        w = Widget(dashboard_id=dashboard_id, name=name, widget_type=widget_type, config=config, position=position)
        self.db.add(w)
        await self.db.flush()
        return w

    async def get(self, widget_id: uuid.UUID) -> Widget | None:
        result = await self.db.execute(select(Widget).where(Widget.id == widget_id))
        return result.scalar_one_or_none()

    async def update(self, widget: Widget, **kwargs) -> Widget:
        for k, v in kwargs.items():
            setattr(widget, k, v)
        await self.db.flush()
        return widget

    async def delete(self, widget: Widget) -> None:
        await self.db.delete(widget)
        await self.db.flush()

    async def update_positions(self, updates: list[dict]) -> None:
        for u in updates:
            widget = await self.get(u["widget_id"])
            if widget:
                widget.position = u["position"]
        await self.db.flush()
