from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClassSessionCreate(BaseModel):
    student_id: int
    topic: str = ""
    raw_note: str = ""
    understanding: int = Field(default=3, ge=1, le=5)
    computation: int = Field(default=3, ge=1, le=5)
    application: int = Field(default=3, ge=1, le=5)
    occurred_at: datetime | None = None


class ClassSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    occurred_at: datetime
    topic: str
    raw_note: str
    structured: dict
    understanding: int
    computation: int
    application: int
    ai_generated: bool
