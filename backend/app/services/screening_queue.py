import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.models.screening_job import ScreeningJob
from app.services.screening_service import screen_application
from app.services.audit_service import record_event

MAX_ATTEMPTS = 3

def enqueue(db: Session, application_id, organization_id):
    existing = db.scalar(select(ScreeningJob).where(
        ScreeningJob.application_id == application_id,
        ScreeningJob.status.in_(["QUEUED", "RUNNING"]),
    ))
    if existing:
        return existing

    job = ScreeningJob(
        id=uuid.uuid4(),
        application_id=application_id,
        organization_id=organization_id,
        status="QUEUED",
        available_at=datetime.now(timezone.utc),
    )
    db.add(job)
    record_event(
        db,
        event_type="SCREENING_QUEUED",
        entity_type="application",
        entity_id=application_id,
        organization_id=organization_id,
    )
    db.commit()
    db.refresh(job)
    return job

def claim_next(db: Session):
    now = datetime.now(timezone.utc)
    candidate = db.scalar(
        select(ScreeningJob)
        .where(
            ScreeningJob.status == "QUEUED",
            ScreeningJob.available_at <= now,
            ScreeningJob.attempts < MAX_ATTEMPTS,
        )
        .order_by(ScreeningJob.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if not candidate:
        return None
    candidate.status = "RUNNING"
    candidate.started_at = now
    candidate.attempts += 1
    db.commit()
    db.refresh(candidate)
    return candidate

def process_one(db: Session):
    job = claim_next(db)
    if not job:
        return None

    try:
        result = screen_application(db, job.application_id, job.organization_id)
        job.status = "COMPLETED"
        job.finished_at = datetime.now(timezone.utc)
        job.last_error = None
        record_event(
            db,
            event_type="SCREENING_COMPLETED",
            entity_type="screening_job",
            entity_id=job.id,
            organization_id=job.organization_id,
            metadata={"score": result.overall_score, "provider": result.provider},
        )
        db.commit()
        return job
    except Exception as exc:
        db.rollback()
        job = db.get(ScreeningJob, job.id)
        if not job:
            return None
        job.status = "FAILED" if job.attempts >= MAX_ATTEMPTS else "QUEUED"
        job.last_error = str(exc)[:2000]
        job.available_at = datetime.now(timezone.utc) + timedelta(seconds=min(300, 15 * job.attempts))
        if job.status == "FAILED":
            job.finished_at = datetime.now(timezone.utc)
        db.commit()
        return job
