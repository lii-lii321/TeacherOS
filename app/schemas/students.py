from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    grade: str = ""
    subject: str = ""
    current_score: int | None = Field(default=None, ge=0, le=750)
    target_score: int | None = Field(default=None, ge=0, le=750)
    teacher_note: str = ""


class StudentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    grade: str | None = None
    subject: str | None = None
    current_score: int | None = Field(default=None, ge=0, le=750)
    target_score: int | None = Field(default=None, ge=0, le=750)
    teacher_note: str | None = None
    status: Literal["active", "archived"] | None = None


class KnowledgePointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    mastery: int
    updated_at: datetime


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    grade: str
    subject: str
    current_score: int | None
    target_score: int | None
    status: str
    teacher_note: str
    created_at: datetime


class StudentProfileOut(BaseModel):
    student: StudentOut
    knowledge_points: list[KnowledgePointOut]
    weak_points: list[str]
    recent_accuracy: float | None = None
    homework_count: int = 0
    session_count: int = 0
