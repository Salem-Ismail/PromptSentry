"""
admin routes - read the audit log over http
"""

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from db import SessionLocal
from models.request_log import RequestLog

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/logs")
def list_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
):
    """paginated request_logs, newest first. needs a valid api key."""
    offset = (page - 1) * limit
    db = SessionLocal()
    try:
        total = db.scalar(select(func.count()).select_from(RequestLog)) or 0

        rows = db.scalars(
            select(RequestLog)
            .order_by(RequestLog.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()

        logs = [
            {
                "id": row.id,
                "request_id": row.request_id,
                "user_id": row.user_id,
                "prompt": row.prompt,
                "response": row.response,
                "threat_type": row.threat_type,
                "layer": row.layer,
                "flagged": row.flagged,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "ip_address": row.ip_address,
                "latency_ms": row.latency_ms,
            }
            for row in rows
        ]

        return {
            "logs": logs,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total else 0,
        }
    finally:
        db.close()
