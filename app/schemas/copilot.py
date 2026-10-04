from pydantic import BaseModel, Field

from app.schemas.classes import ClassSessionOut
from app.schemas.homework import HomeworkOut


class LessonNoteIn(BaseModel):
    student_id: int
    note: str = Field(min_length=2, max_length=4000)
    create_records: bool = True


class CopilotResultOut(BaseModel):
    structured: dict
    parent_message: str
    homework_estimated_minutes: int
    session: ClassSessionOut | None = None
    homework: HomeworkOut | None = None
