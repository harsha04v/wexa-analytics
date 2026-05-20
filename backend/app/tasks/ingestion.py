from __future__ import annotations

import asyncio
import csv
import io
import uuid
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.core.database import async_session_factory
from app.models.event import Event
from app.models.ingestion_job import JobStatus
from app.repositories.ingestion import EventRepository, IngestionJobRepository

import structlog

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_batch_ingestion(self, job_id: str, org_id: str, events_data: list[dict]):
    """Process batch event ingestion asynchronously."""
    asyncio.run(_process_batch(job_id, org_id, events_data))


async def _process_batch(job_id: str, org_id: str, events_data: list[dict]):
    async with async_session_factory() as db:
        job_repo = IngestionJobRepository(db)
        event_repo = EventRepository(db)

        job = await job_repo.get(uuid.UUID(job_id), uuid.UUID(org_id))
        if not job:
            logger.error("batch_job_not_found", job_id=job_id)
            return

        await job_repo.update_status(job, status=JobStatus.PROCESSING)

        events = []
        failed = 0
        errors = []

        for i, ed in enumerate(events_data):
            try:
                ts = ed.get("timestamp")
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                elif ts is None:
                    ts = datetime.now(timezone.utc)

                events.append(
                    Event(
                        organization_id=uuid.UUID(org_id),
                        event_name=ed["event_name"],
                        properties=ed.get("properties"),
                        timestamp=ts,
                        data_source_id=uuid.UUID(ed["data_source_id"]) if ed.get("data_source_id") else None,
                    )
                )
            except Exception as e:
                failed += 1
                errors.append(f"Row {i}: {str(e)}")

        if events:
            await event_repo.create_many(events)

        final_status = JobStatus.COMPLETED if failed == 0 else JobStatus.COMPLETED
        await job_repo.update_status(
            job, status=final_status, processed=len(events), failed=failed,
            error_details={"errors": errors[:50]} if errors else None,
        )
        await db.commit()

        logger.info("batch_ingestion_complete", job_id=job_id, processed=len(events), failed=failed)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_csv_ingestion(self, job_id: str, org_id: str, csv_content: str):
    """Process CSV file ingestion asynchronously."""
    asyncio.run(_process_csv(job_id, org_id, csv_content))


async def _process_csv(job_id: str, org_id: str, csv_content: str):
    async with async_session_factory() as db:
        job_repo = IngestionJobRepository(db)
        event_repo = EventRepository(db)

        job = await job_repo.get(uuid.UUID(job_id), uuid.UUID(org_id))
        if not job:
            logger.error("csv_job_not_found", job_id=job_id)
            return

        await job_repo.update_status(job, status=JobStatus.PROCESSING)

        reader = csv.DictReader(io.StringIO(csv_content))
        events = []
        failed = 0
        errors = []

        for i, row in enumerate(reader):
            try:
                event_name = row.get("event_name", "").strip()
                if not event_name:
                    raise ValueError("missing event_name")

                ts_str = row.get("timestamp")
                ts = datetime.fromisoformat(ts_str) if ts_str else datetime.now(timezone.utc)
                props = {k: v for k, v in row.items() if k not in ("event_name", "timestamp")}

                events.append(
                    Event(
                        organization_id=uuid.UUID(org_id),
                        event_name=event_name,
                        properties=props if props else None,
                        timestamp=ts,
                    )
                )
            except Exception as e:
                failed += 1
                errors.append(f"Row {i+1}: {str(e)}")

        if events:
            await event_repo.create_many(events)

        final_status = JobStatus.COMPLETED if len(events) > 0 else JobStatus.FAILED
        await job_repo.update_status(
            job, status=final_status, processed=len(events), failed=failed,
            error_details={"errors": errors[:50]} if errors else None,
        )
        await db.commit()

        logger.info("csv_ingestion_complete", job_id=job_id, processed=len(events), failed=failed)
