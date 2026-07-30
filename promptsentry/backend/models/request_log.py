"""
request_logs table - one row per request through the proxy
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # hashed api key
    prompt: Mapped[str] = mapped_column(Text)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    threat_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    layer: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 or 2 if blocked
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
