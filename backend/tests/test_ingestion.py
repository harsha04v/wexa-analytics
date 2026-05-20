"""Tests for data ingestion endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_api_key(client: AsyncClient, owner_setup):
    headers, _, _ = owner_setup
    res = await client.post("/api/v1/ingestion/api-keys", headers=headers, json={
        "name": "Production Key",
    })
    assert res.status_code == 201
    assert res.json()["name"] == "Production Key"
    assert "raw_key" in res.json()


async def test_ingest_single_event(client: AsyncClient, owner_setup):
    headers, _, _ = owner_setup
    # Create an API key first
    key_res = await client.post(
        "/api/v1/ingestion/api-keys", headers=headers, json={"name": "Ingest Key"}
    )
    raw_key = key_res.json()["raw_key"]

    res = await client.post("/api/v1/ingestion/events/single", headers={
        "X-API-Key": raw_key,
    }, json={
        "event_name": "page_view",
        "properties": {"page": "/home"},
    })
    assert res.status_code == 201
    assert res.json()["event_name"] == "page_view"


async def test_ingest_without_api_key(client: AsyncClient):
    res = await client.post("/api/v1/ingestion/events/single", json={
        "event_name": "page_view",
    })
    assert res.status_code in (401, 403)


async def test_csv_upload(client: AsyncClient, owner_setup):
    headers, _, _ = owner_setup
    csv_content = "event_name,timestamp,page\npage_view,2026-05-20T10:00:00,/home\n"
    res = await client.post(
        "/api/v1/ingestion/upload-csv",
        headers=headers,
        files={"file": ("events.csv", csv_content, "text/csv")},
    )
    assert res.status_code == 200


async def test_create_data_source(client: AsyncClient, owner_setup):
    headers, _, _ = owner_setup
    res = await client.post("/api/v1/ingestion/data-sources", headers=headers, json={
        "name": "Web App",
        "source_type": "api",
    })
    assert res.status_code == 201
    assert res.json()["name"] == "Web App"
