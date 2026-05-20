from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_api_key
from app.models.data_source import DataSourceType
from app.models.event import Event
from app.models.ingestion_job import JobStatus, JobType
from app.repositories.ingestion import (
    ApiKeyRepository,
    DataSourceRepository,
    EventRepository,
    IngestionJobRepository,
)
from app.schemas.ingestion import EventCreate


class IngestionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.api_keys = ApiKeyRepository(db)
        self.data_sources = DataSourceRepository(db)
        self.events = EventRepository(db)
        self.jobs = IngestionJobRepository(db)

    # --- API Key management ---

    async def create_api_key(self, *, org_id: uuid.UUID, name: str, created_by: uuid.UUID) -> dict:
        raw_key, key_hash = generate_api_key()
        key_prefix = raw_key[:8]
        api_key = await self.api_keys.create(
            org_id=org_id, name=name, key_prefix=key_prefix, key_hash=key_hash, created_by=created_by
        )
        return {
            "id": api_key.id,
            "name": api_key.name,
            "key_prefix": api_key.key_prefix,
            "raw_key": raw_key,
            "created_at": api_key.created_at,
            "last_used_at": api_key.last_used_at,
            "expires_at": api_key.expires_at,
            "is_active": api_key.is_active,
        }

    async def list_api_keys(self, org_id: uuid.UUID) -> list:
        return await self.api_keys.list_by_org(org_id)

    async def revoke_api_key(self, api_key_id: uuid.UUID, org_id: uuid.UUID) -> None:
        keys = await self.api_keys.list_by_org(org_id)
        target = next((k for k in keys if k.id == api_key_id), None)
        if not target:
            raise NotFoundError("API Key")
        await self.api_keys.revoke(target)

    # --- Data Sources ---

    async def create_data_source(
        self, *, org_id: uuid.UUID, name: str, source_type: str, config: dict | None, created_by: uuid.UUID
    ):
        return await self.data_sources.create(
            org_id=org_id, name=name, source_type=DataSourceType(source_type), config=config, created_by=created_by
        )

    async def list_data_sources(self, org_id: uuid.UUID):
        return await self.data_sources.list_by_org(org_id)

    # --- Event ingestion ---

    async def ingest_single(self, *, org_id: uuid.UUID, data: EventCreate, created_by: uuid.UUID) -> Event:
        event = Event(
            organization_id=org_id,
            event_name=data.event_name,
            properties=data.properties,
            timestamp=data.timestamp or datetime.now(timezone.utc),
            data_source_id=data.data_source_id,
        )
        self.db.add(event)
        await self.db.flush()

        await self.jobs.create(
            org_id=org_id, job_type=JobType.SINGLE, created_by=created_by, total_records=1
        )

        return event

    async def ingest_batch(
        self, *, org_id: uuid.UUID, events_data: list[EventCreate], created_by: uuid.UUID
    ) -> dict:
        job = await self.jobs.create(
            org_id=org_id, job_type=JobType.BATCH, created_by=created_by, total_records=len(events_data)
        )

        events = []
        failed = 0
        for ed in events_data:
            try:
                events.append(
                    Event(
                        organization_id=org_id,
                        event_name=ed.event_name,
                        properties=ed.properties,
                        timestamp=ed.timestamp or datetime.now(timezone.utc),
                        data_source_id=ed.data_source_id,
                    )
                )
            except Exception:
                failed += 1

        if events:
            await self.events.create_many(events)

        await self.jobs.update_status(
            job,
            status=JobStatus.COMPLETED,
            processed=len(events),
            failed=failed,
        )

        return {
            "job_id": job.id,
            "total": len(events_data),
            "processed": len(events),
            "failed": failed,
        }

    async def ingest_csv(
        self, *, org_id: uuid.UUID, file_content: bytes, created_by: uuid.UUID
    ) -> dict:
        try:
            text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            raise ValidationError("CSV must be UTF-8 encoded")

        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)

        if not rows:
            raise ValidationError("CSV file is empty")

        if "event_name" not in (reader.fieldnames or []):
            raise ValidationError("CSV must have an 'event_name' column")

        job = await self.jobs.create(
            org_id=org_id, job_type=JobType.CSV, created_by=created_by, total_records=len(rows)
        )

        events = []
        failed = 0
        errors = []
        for i, row in enumerate(rows):
            try:
                event_name = row.get("event_name", "").strip()
                if not event_name:
                    raise ValueError(f"Row {i+1}: missing event_name")

                ts_str = row.get("timestamp")
                ts = datetime.fromisoformat(ts_str) if ts_str else datetime.now(timezone.utc)

                props = {k: v for k, v in row.items() if k not in ("event_name", "timestamp")}

                events.append(
                    Event(
                        organization_id=org_id,
                        event_name=event_name,
                        properties=props if props else None,
                        timestamp=ts,
                    )
                )
            except Exception as e:
                failed += 1
                errors.append(str(e))

        if events:
            await self.events.create_many(events)

        status = JobStatus.COMPLETED if failed == 0 else (JobStatus.FAILED if len(events) == 0 else JobStatus.COMPLETED)
        await self.jobs.update_status(
            job,
            status=status,
            processed=len(events),
            failed=failed,
            error_details={"errors": errors[:50]} if errors else None,
        )

        return {
            "job_id": job.id,
            "total": len(rows),
            "processed": len(events),
            "failed": failed,
        }

    async def list_jobs(self, org_id: uuid.UUID):
        return await self.jobs.list_by_org(org_id)

    async def get_job(self, job_id: uuid.UUID, org_id: uuid.UUID):
        job = await self.jobs.get(job_id, org_id)
        if not job:
            raise NotFoundError("Ingestion Job")
        return job
