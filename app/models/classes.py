from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.clock import utcnow


class ClassSession(Base):
    __tablename__ = "class_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    topic: Mapped[str] = mapped_column(String(128), default="")
    raw_note: Mapped[str] = mapped_column(String(4096), default="")
    structured: Mapped[dict] = mapped_column(JSON, default=dict)
    understanding: Mapped[int] = mapped_column(Integer, default=3)
    computation: Mapped[int] = mapped_column(Integer, default=3)
    application: Mapped[int] = mapped_column(Integer, default=3)
    ai_generated: Mapped[bool] = mapped_column(default=False)
