from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_api_key_org, get_current_org_membership, require_roles
from app.models.api_key import ApiKey
from app.models.membership import Membership, Role
from app.schemas.ingestion import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    BatchEventCreate,
    DataSourceCreate,
    DataSourceResponse,
    EventCreate,
    EventResponse,
    IngestionJobResponse,
)
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


# --- Ingestion endpoints (API key auth) ---

@router.post("/events/single", response_model=EventResponse, status_code=201)
async def ingest_single(
    data: EventCreate,
    api_key: ApiKey = Depends(get_api_key_org),
    db: AsyncSession = Depends(get_db),
):
    svc = IngestionService(db)
    return await svc.ingest_single(
        org_id=api_key.organization_id, data=data, created_by=api_key.created_by
    )


@router.post("/events/batch")
async def ingest_batch(
    data: BatchEventCreate,
    api_key: ApiKey = Depends(get_api_key_org),
    db: AsyncSession = Depends(get_db),
):
    svc = IngestionService(db)
    return await svc.ingest_batch(
        org_id=api_key.organization_id, events_data=data.events, created_by=api_key.created_by
    )


@router.post("/events/csv")
async def ingest_csv(
    file: UploadFile = File(...),
    api_key: ApiKey = Depends(get_api_key_org),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    svc = IngestionService(db)
    return await svc.ingest_csv(
        org_id=api_key.organization_id, file_content=content, created_by=api_key.created_by
    )


@router.post("/upload-csv")
async def upload_csv_jwt(
    file: UploadFile = File(...),
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """CSV upload authenticated via JWT (used by the frontend UI)."""
    content = await file.read()
    svc = IngestionService(db)
    return await svc.ingest_csv(
        org_id=membership.organization_id, file_content=content, created_by=membership.user_id
    )


# --- JWT-authenticated ingestion management ---

@router.post("/api-keys", status_code=201)
async def create_api_key(
    data: ApiKeyCreate,
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    svc = IngestionService(db)
    return await svc.create_api_key(
        org_id=membership.organization_id, name=data.name, created_by=membership.user_id
    )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    svc = IngestionService(db)
    return await svc.list_api_keys(membership.organization_id)


@router.delete("/api-keys/{api_key_id}", status_code=204)
async def revoke_api_key(
    api_key_id: uuid.UUID,
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    svc = IngestionService(db)
    await svc.revoke_api_key(api_key_id, membership.organization_id)


@router.post("/data-sources", response_model=DataSourceResponse, status_code=201)
async def create_data_source(
    data: DataSourceCreate,
    membership: Membership = Depends(require_roles(Role.OWNER, Role.ADMIN, Role.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    svc = IngestionService(db)
    return await svc.create_data_source(
        org_id=membership.organization_id,
        name=data.name,
        source_type=data.source_type,
        config=data.config,
        created_by=membership.user_id,
    )


@router.get("/data-sources", response_model=list[DataSourceResponse])
async def list_data_sources(
    membership: Membership = Depends(get_current_org_membership),
    db: AsyncSession = Depends(get_db),
):
    svc = IngestionService(db)
    return await svc.list_data_sources(membership.organization_id)


@router.get("/jobs", response_model=list[IngestionJobResponse])
async def list_jobs(
    membership: Membership = Depends(get_current_org_membership),
    db: AsyncSession = Depends(get_db),
):
    svc = IngestionService(db)
    return await svc.list_jobs(membership.organization_id)


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
async def get_job(
    job_id: uuid.UUID,
    membership: Membership = Depends(get_current_org_membership),
    db: AsyncSession = Depends(get_db),
):
    svc = IngestionService(db)
    return await svc.get_job(job_id, membership.organization_id)
