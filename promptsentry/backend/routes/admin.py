"""
admin routes - read the audit log over http
"""

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select

from db import SessionLocal
from models.request_log import RequestLog

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/logs")
def list_logs(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
):
    """
    paginated request_logs for THIS api key only (newest first).
    user_id is the hashed key set by gatekeeping - never the raw secret.
    """
    user_id = getattr(request.state, "user_id", None)
    # fail closed: never dump the whole table if identity is missing
    if not user_id:
        return {"logs": [], "total": 0, "page": page, "limit": limit, "pages": 0}

    offset = (page - 1) * limit
    db = SessionLocal()
    try:
        filt = RequestLog.user_id == user_id
        count_stmt = select(func.count()).select_from(RequestLog).where(filt)
        list_stmt = (
            select(RequestLog)
            .where(filt)
            .order_by(RequestLog.id.desc())
        )

        total = db.scalar(count_stmt) or 0
        rows = db.scalars(list_stmt.offset(offset).limit(limit)).all()

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
