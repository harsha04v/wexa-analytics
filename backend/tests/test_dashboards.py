"""Tests for dashboards, widgets, and analytics endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_dashboard(client: AsyncClient, owner_setup):
    headers, _, _ = owner_setup
    res = await client.post("/api/v1/dashboards", headers=headers, json={
        "name": "Sales Dashboard",
        "description": "Revenue metrics",
    })
    assert res.status_code == 201
    assert res.json()["name"] == "Sales Dashboard"
    assert res.json()["widgets"] == []


async def test_add_widget(client: AsyncClient, owner_setup):
    headers, _, _ = owner_setup
    dash = await client.post("/api/v1/dashboards", headers=headers, json={"name": "Widget Test"})
    dashboard_id = dash.json()["id"]

    res = await client.post(f"/api/v1/dashboards/{dashboard_id}/widgets", headers=headers, json={
        "name": "Page Views",
        "widget_type": "line_chart",
        "config": {"event_name": "page_view"},
        "position": {"x": 0, "y": 0, "w": 6, "h": 4},
    })
    assert res.status_code == 201
    assert res.json()["widget_type"] == "line_chart"


async def test_public_sharing(client: AsyncClient, owner_setup):
    headers, _, _ = owner_setup
    dash = await client.post("/api/v1/dashboards", headers=headers, json={"name": "Public Test"})
    dashboard_id = dash.json()["id"]

    # Toggle public on
    toggle = await client.post(f"/api/v1/dashboards/{dashboard_id}/toggle-public", headers=headers)
    assert toggle.json()["is_public"] is True
    share_token = toggle.json()["share_token"]

    # Access without auth via share token
    public = await client.get(f"/api/v1/dashboards/public/{share_token}")
    assert public.status_code == 200
    assert public.json()["name"] == "Public Test"


async def test_analytics_time_series(client: AsyncClient, owner_setup):
    headers, _, _ = owner_setup
    res = await client.get("/api/v1/dashboards/analytics/time-series", headers=headers)
    assert res.status_code == 200
    assert "data" in res.json()


async def test_viewer_cannot_create_dashboard(client: AsyncClient, viewer_setup):
    headers, _, _ = viewer_setup
    res = await client.post("/api/v1/dashboards", headers=headers, json={"name": "Blocked"})
    assert res.status_code == 403


async def test_health(client: AsyncClient):
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
