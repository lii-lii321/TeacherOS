from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.clock import utcnow


class MasteryLog(Base):
    __tablename__ = "mastery_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    mastery: Mapped[int] = mapped_column(Integer)
    observed: Mapped[int | None] = mapped_column(Integer, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
