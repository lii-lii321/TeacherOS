from pydantic import BaseModel, ConfigDict, Field, field_validator


class HomeworkItemIn(BaseModel):
    knowledge_point: str = Field(min_length=1, max_length=64)
    difficulty: str = "basic"
    question: str = ""
    answer: str | None = None

    @field_validator("knowledge_point")
    @classmethod
    def _clean_knowledge_point(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("knowledge_point must not be blank")
        return value


class HomeworkCreate(BaseModel):
    student_id: int
    title: str = ""
    items: list[HomeworkItemIn] = Field(min_length=1)


class SubmitItem(BaseModel):
    item_id: int
    correct: bool


class SubmitResults(BaseModel):
    results: list[SubmitItem] = Field(min_length=1)


class SubmitAnswers(BaseModel):
    answers: list[str] = Field(min_length=1)


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
