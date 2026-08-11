from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession

router = APIRouter(tags=["System"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "hirelens-api"}


@router.get("/ready")
def readiness(db: DbSession):
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
