from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.clock import utcnow


class Homework(Base):
    __tablename__ = "homework"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("class_sessions.id"), default=None)
    title: Mapped[str] = mapped_column(String(128), default="")
    items: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="assigned")
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    graded: Mapped[dict | None] = mapped_column(JSON, default=None)
