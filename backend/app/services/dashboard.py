from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.dashboard import WidgetType
from app.repositories.dashboard import DashboardRepository, WidgetRepository
from app.repositories.ingestion import EventRepository


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.dashboards = DashboardRepository(db)
        self.widgets = WidgetRepository(db)
        self.events = EventRepository(db)

    async def create_dashboard(
        self, *, org_id: uuid.UUID, name: str, description: str | None, created_by: uuid.UUID
    ):
        return await self.dashboards.create(org_id=org_id, name=name, description=description, created_by=created_by)

    async def list_dashboards(self, org_id: uuid.UUID):
        dashboards = await self.dashboards.list_by_org(org_id)
        result = []
        for d in dashboards:
            result.append({
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "is_public": d.is_public,
                "created_at": d.created_at,
                "widget_count": len(d.widgets) if d.widgets else 0,
            })
        return result

    async def get_dashboard(self, dashboard_id: uuid.UUID, org_id: uuid.UUID):
        d = await self.dashboards.get(dashboard_id, org_id)
        if not d:
            raise NotFoundError("Dashboard")
        return d

    async def get_public_dashboard(self, share_token: str):
        d = await self.dashboards.get_by_share_token(share_token)
        if not d:
            raise NotFoundError("Dashboard")
        return d

    async def update_dashboard(self, dashboard_id: uuid.UUID, org_id: uuid.UUID, **kwargs):
        d = await self.dashboards.get(dashboard_id, org_id)
        if not d:
            raise NotFoundError("Dashboard")
        return await self.dashboards.update(d, **kwargs)

    async def delete_dashboard(self, dashboard_id: uuid.UUID, org_id: uuid.UUID):
        d = await self.dashboards.get(dashboard_id, org_id)
        if not d:
            raise NotFoundError("Dashboard")
        await self.dashboards.delete(d)

    async def toggle_public(self, dashboard_id: uuid.UUID, org_id: uuid.UUID):
        d = await self.dashboards.get(dashboard_id, org_id)
        if not d:
            raise NotFoundError("Dashboard")
        return await self.dashboards.toggle_public(d)

    # --- Widgets ---

    async def create_widget(
        self, *, dashboard_id: uuid.UUID, org_id: uuid.UUID, name: str,
        widget_type: str, config: dict, position: dict
    ):
        d = await self.dashboards.get(dashboard_id, org_id)
        if not d:
            raise NotFoundError("Dashboard")
        return await self.widgets.create(
            dashboard_id=dashboard_id, name=name,
            widget_type=WidgetType(widget_type), config=config, position=position
        )

    async def update_widget(self, widget_id: uuid.UUID, dashboard_id: uuid.UUID, org_id: uuid.UUID, **kwargs):
        d = await self.dashboards.get(dashboard_id, org_id)
        if not d:
            raise NotFoundError("Dashboard")
        w = await self.widgets.get(widget_id)
        if not w or w.dashboard_id != dashboard_id:
            raise NotFoundError("Widget")
        if "widget_type" in kwargs and kwargs["widget_type"]:
            kwargs["widget_type"] = WidgetType(kwargs["widget_type"])
        clean = {k: v for k, v in kwargs.items() if v is not None}
        return await self.widgets.update(w, **clean)

    async def delete_widget(self, widget_id: uuid.UUID, dashboard_id: uuid.UUID, org_id: uuid.UUID):
        d = await self.dashboards.get(dashboard_id, org_id)
        if not d:
            raise NotFoundError("Dashboard")
        w = await self.widgets.get(widget_id)
        if not w or w.dashboard_id != dashboard_id:
            raise NotFoundError("Widget")
        await self.widgets.delete(w)

    async def update_layout(self, dashboard_id: uuid.UUID, org_id: uuid.UUID, layouts: list[dict]):
        d = await self.dashboards.get(dashboard_id, org_id)
        if not d:
            raise NotFoundError("Dashboard")
        await self.widgets.update_positions(layouts)

    # --- Aggregation queries for widgets ---

    async def query_time_series(self, org_id: uuid.UUID, **kwargs):
        return await self.events.time_series(org_id, **kwargs)

    async def query_top_events(self, org_id: uuid.UUID, **kwargs):
        return await self.events.top_events(org_id, **kwargs)

    async def query_kpi(self, org_id: uuid.UUID, **kwargs):
        return await self.events.kpi(org_id, **kwargs)

    async def query_events_list(self, org_id: uuid.UUID, **kwargs):
        return await self.events.list_events(org_id, **kwargs)
