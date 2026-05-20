from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_org_membership, require_roles
from app.models.membership import Membership, Role
from app.schemas.dashboard import (
    AggregationResponse,
    DashboardCreate,
    DashboardListResponse,
    DashboardResponse,
    DashboardUpdate,
    WidgetCreate,
    WidgetLayoutUpdate,
    WidgetResponse,
    WidgetUpdate,
)
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.post("", response_model=DashboardResponse, status_code=201)
async def create_dashboard(
    data: DashboardCreate,
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    svc = DashboardService(db)
    return await svc.create_dashboard(
        org_id=membership.organization_id,
        name=data.name,
        description=data.description,
        created_by=membership.user_id,
    )


@router.get("", response_model=list[DashboardListResponse])
async def list_dashboards(
    membership: Membership = Depends(get_current_org_membership),
    db: AsyncSession = Depends(get_db),
):
    svc = DashboardService(db)
    return await svc.list_dashboards(membership.organization_id)


@router.get("/public/{share_token}", response_model=DashboardResponse)
async def get_public_dashboard(share_token: str, db: AsyncSession = Depends(get_db)):
    svc = DashboardService(db)
    return await svc.get_public_dashboard(share_token)


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: uuid.UUID,
    membership: Membership = Depends(get_current_org_membership),
    db: AsyncSession = Depends(get_db),
):
    svc = DashboardService(db)
    return await svc.get_dashboard(dashboard_id, membership.organization_id)


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: uuid.UUID,
    data: DashboardUpdate,
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    svc = DashboardService(db)
    update_data = data.model_dump(exclude_unset=True)
    return await svc.update_dashboard(dashboard_id, membership.organization_id, **update_data)


@router.delete("/{dashboard_id}", status_code=204)
async def delete_dashboard(
    dashboard_id: uuid.UUID,
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    svc = DashboardService(db)
    await svc.delete_dashboard(dashboard_id, membership.organization_id)


@router.post("/{dashboard_id}/toggle-public", response_model=DashboardResponse)
async def toggle_public(
    dashboard_id: uuid.UUID,
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    svc = DashboardService(db)
    return await svc.toggle_public(dashboard_id, membership.organization_id)


# --- Widgets ---

@router.post("/{dashboard_id}/widgets", response_model=WidgetResponse, status_code=201)
async def create_widget(
    dashboard_id: uuid.UUID,
    data: WidgetCreate,
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    svc = DashboardService(db)
    return await svc.create_widget(
        dashboard_id=dashboard_id,
        org_id=membership.organization_id,
        name=data.name,
        widget_type=data.widget_type,
        config=data.config,
        position=data.position,
    )


@router.patch("/{dashboard_id}/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    data: WidgetUpdate,
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    svc = DashboardService(db)
    update_data = data.model_dump(exclude_unset=True)
    return await svc.update_widget(widget_id, dashboard_id, membership.organization_id, **update_data)


@router.delete("/{dashboard_id}/widgets/{widget_id}", status_code=204)
async def delete_widget(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    svc = DashboardService(db)
    await svc.delete_widget(widget_id, dashboard_id, membership.organization_id)


@router.put("/{dashboard_id}/layout")
async def update_layout(
    dashboard_id: uuid.UUID,
    data: WidgetLayoutUpdate,
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    svc = DashboardService(db)
    layouts = [{"widget_id": l.widget_id, "position": l.position} for l in data.layouts]
    await svc.update_layout(dashboard_id, membership.organization_id, layouts)
    return {"status": "ok"}


# --- Analytics / Aggregation ---

@router.get("/analytics/time-series")
async def analytics_time_series(
    membership: Membership = Depends(get_current_org_membership),
    db: AsyncSession = Depends(get_db),
    event_name: str | None = None,
    data_source_id: uuid.UUID | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    interval: str = "day",
):
    svc = DashboardService(db)
    data = await svc.query_time_series(
        membership.organization_id,
        event_name=event_name,
        data_source_id=data_source_id,
        start_time=start_time,
        end_time=end_time,
        interval=interval,
    )
    return {"data": data, "total": len(data)}


@router.get("/analytics/top-events")
async def analytics_top_events(
    membership: Membership = Depends(get_current_org_membership),
    db: AsyncSession = Depends(get_db),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(default=10, ge=1, le=100),
):
    svc = DashboardService(db)
    data = await svc.query_top_events(
        membership.organization_id, start_time=start_time, end_time=end_time, limit=limit
    )
    return {"data": data, "total": len(data)}


@router.get("/analytics/kpi")
async def analytics_kpi(
    membership: Membership = Depends(get_current_org_membership),
    db: AsyncSession = Depends(get_db),
    event_name: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
):
    svc = DashboardService(db)
    return await svc.query_kpi(
        membership.organization_id, event_name=event_name, start_time=start_time, end_time=end_time
    )


@router.get("/analytics/events")
async def analytics_events(
    membership: Membership = Depends(get_current_org_membership),
    db: AsyncSession = Depends(get_db),
    event_name: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    svc = DashboardService(db)
    events = await svc.query_events_list(
        membership.organization_id,
        event_name=event_name,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    return {"data": [EventResponseInline.model_validate(e) for e in events], "total": len(events)}


from app.schemas.ingestion import EventResponse as EventResponseInline
