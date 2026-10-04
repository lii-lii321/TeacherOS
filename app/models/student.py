from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.clock import utcnow


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    grade: Mapped[str] = mapped_column(String(32), default="")
    subject: Mapped[str] = mapped_column(String(32), default="")
    current_score: Mapped[int | None] = mapped_column(Integer, default=None)
    target_score: Mapped[int | None] = mapped_column(Integer, default=None)
    status: Mapped[str] = mapped_column(String(16), default="active")
    teacher_note: Mapped[str] = mapped_column(String(1024), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    knowledge_points: Mapped[list["KnowledgePoint"]] = relationship(back_populates="student")


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"
    __table_args__ = (UniqueConstraint("student_id", "name", name="uq_kp_student_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    mastery: Mapped[int] = mapped_column(Integer, default=50)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    student: Mapped["Student"] = relationship(back_populates="knowledge_points")
