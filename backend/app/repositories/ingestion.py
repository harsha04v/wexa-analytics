from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.models.data_source import DataSource, DataSourceType
from app.models.event import Event
from app.models.ingestion_job import IngestionJob, JobStatus, JobType


class ApiKeyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, *, org_id: uuid.UUID, name: str, key_prefix: str, key_hash: str, created_by: uuid.UUID
    ) -> ApiKey:
        ak = ApiKey(
            organization_id=org_id, name=name, key_prefix=key_prefix, key_hash=key_hash, created_by=created_by
        )
        self.db.add(ak)
        await self.db.flush()
        return ak

    async def list_by_org(self, org_id: uuid.UUID) -> list[ApiKey]:
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.organization_id == org_id, ApiKey.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def revoke(self, api_key: ApiKey) -> None:
        api_key.is_active = False
        await self.db.flush()

    async def update_last_used(self, api_key: ApiKey) -> None:
        api_key.last_used_at = datetime.now(timezone.utc)
        await self.db.flush()


class DataSourceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, *, org_id: uuid.UUID, name: str, source_type: DataSourceType, config: dict | None, created_by: uuid.UUID
    ) -> DataSource:
        ds = DataSource(
            organization_id=org_id, name=name, source_type=source_type, config=config, created_by=created_by
        )
        self.db.add(ds)
        await self.db.flush()
        return ds

    async def list_by_org(self, org_id: uuid.UUID) -> list[DataSource]:
        result = await self.db.execute(
            select(DataSource).where(DataSource.organization_id == org_id, DataSource.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def get(self, ds_id: uuid.UUID, org_id: uuid.UUID) -> DataSource | None:
        result = await self.db.execute(
            select(DataSource).where(
                DataSource.id == ds_id, DataSource.organization_id == org_id, DataSource.is_active.is_(True)
            )
        )
        return result.scalar_one_or_none()


class EventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_many(self, events: list[Event]) -> int:
        self.db.add_all(events)
        await self.db.flush()
        return len(events)

    async def count_by_org(self, org_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Event).where(Event.organization_id == org_id)
        )
        return result.scalar_one()

    async def time_series(
        self,
        org_id: uuid.UUID,
        *,
        event_name: str | None = None,
        data_source_id: uuid.UUID | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        interval: str = "day",
    ) -> list[dict]:
        trunc_map = {"hour": "hour", "day": "day", "week": "week", "month": "month"}
        trunc = trunc_map.get(interval, "day")

        bucket = func.date_trunc(trunc, Event.timestamp).label("bucket")
        q = select(bucket, func.count().label("count")).where(Event.organization_id == org_id)

        if event_name:
            q = q.where(Event.event_name == event_name)
        if data_source_id:
            q = q.where(Event.data_source_id == data_source_id)
        if start_time:
            q = q.where(Event.timestamp >= start_time)
        if end_time:
            q = q.where(Event.timestamp <= end_time)

        q = q.group_by(bucket).order_by(bucket)
        result = await self.db.execute(q)
        return [{"timestamp": str(row.bucket), "value": row.count} for row in result.all()]

    async def top_events(
        self,
        org_id: uuid.UUID,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 10,
    ) -> list[dict]:
        q = (
            select(Event.event_name, func.count().label("count"))
            .where(Event.organization_id == org_id)
        )
        if start_time:
            q = q.where(Event.timestamp >= start_time)
        if end_time:
            q = q.where(Event.timestamp <= end_time)
        q = q.group_by(Event.event_name).order_by(func.count().desc()).limit(limit)
        result = await self.db.execute(q)
        return [{"event_name": row.event_name, "count": row.count} for row in result.all()]

    async def kpi(
        self,
        org_id: uuid.UUID,
        *,
        event_name: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict:
        q = select(func.count().label("total")).where(Event.organization_id == org_id)
        if event_name:
            q = q.where(Event.event_name == event_name)
        if start_time:
            q = q.where(Event.timestamp >= start_time)
        if end_time:
            q = q.where(Event.timestamp <= end_time)
        result = await self.db.execute(q)
        total = result.scalar_one()
        return {"total_events": total}

    async def list_events(
        self,
        org_id: uuid.UUID,
        *,
        event_name: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Event]:
        q = select(Event).where(Event.organization_id == org_id)
        if event_name:
            q = q.where(Event.event_name == event_name)
        if start_time:
            q = q.where(Event.timestamp >= start_time)
        if end_time:
            q = q.where(Event.timestamp <= end_time)
        q = q.order_by(Event.timestamp.desc()).limit(limit).offset(offset)
        result = await self.db.execute(q)
        return list(result.scalars().all())


class IngestionJobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, *, org_id: uuid.UUID, job_type: JobType, created_by: uuid.UUID,
        data_source_id: uuid.UUID | None = None, total_records: int = 0
    ) -> IngestionJob:
        job = IngestionJob(
            organization_id=org_id, data_source_id=data_source_id,
            job_type=job_type, created_by=created_by, total_records=total_records
        )
        self.db.add(job)
        await self.db.flush()
        return job

    async def get(self, job_id: uuid.UUID, org_id: uuid.UUID) -> IngestionJob | None:
        result = await self.db.execute(
            select(IngestionJob).where(IngestionJob.id == job_id, IngestionJob.organization_id == org_id)
        )
        return result.scalar_one_or_none()

    async def list_by_org(self, org_id: uuid.UUID, limit: int = 20) -> list[IngestionJob]:
        result = await self.db.execute(
            select(IngestionJob)
            .where(IngestionJob.organization_id == org_id)
            .order_by(IngestionJob.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self, job: IngestionJob, *, status: JobStatus,
        processed: int = 0, failed: int = 0, error_details: dict | None = None
    ) -> None:
        job.status = status
        job.processed_records = processed
        job.failed_records = failed
        job.error_details = error_details
        if status == JobStatus.PROCESSING:
            job.started_at = datetime.now(timezone.utc)
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
            job.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
