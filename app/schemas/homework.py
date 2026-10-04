from pydantic import BaseModel, ConfigDict, Field


class HomeworkItemIn(BaseModel):
    knowledge_point: str = Field(min_length=1)
    difficulty: str = "basic"
    question: str = ""


class HomeworkCreate(BaseModel):
    student_id: int
    title: str = ""
    items: list[HomeworkItemIn] = Field(min_length=1)


class SubmitItem(BaseModel):
    item_id: int
    correct: bool


class SubmitResults(BaseModel):
    results: list[SubmitItem] = Field(min_length=1)


class HomeworkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    session_id: int | None
    title: str
    items: list[dict]
    status: str
    graded: dict | None


class GradeOut(BaseModel):
    homework_id: int
    accuracy: float
    knowledge_updates: list[dict]
