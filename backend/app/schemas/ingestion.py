from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    event_name: str = Field(min_length=1, max_length=255)
    properties: dict | None = None
    timestamp: datetime | None = None
    data_source_id: uuid.UUID | None = None


class BatchEventCreate(BaseModel):
    events: list[EventCreate] = Field(min_length=1, max_length=10000)


class EventResponse(BaseModel):
    id: uuid.UUID
    event_name: str
    properties: dict | None
    timestamp: datetime
    data_source_id: uuid.UUID | None
    ingested_at: datetime

    model_config = {"from_attributes": True}


class IngestionJobResponse(BaseModel):
    id: uuid.UUID
    job_type: str
    status: str
    total_records: int
    processed_records: int
    failed_records: int
    error_details: dict | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class DataSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source_type: str = Field(pattern="^(api|csv|webhook)$")
    config: dict | None = None


class DataSourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    source_type: str
    config: dict | None
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None
    is_active: bool

    model_config = {"from_attributes": True}


class ApiKeyCreatedResponse(ApiKeyResponse):
    raw_key: str  # Only returned on creation
