from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    student_id: int
    amount: float = Field(gt=0)
    kind: Literal["income", "expense"] = "income"
    note: str = ""


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    amount: float
    kind: str
    note: str


class BusinessSummaryOut(BaseModel):
    month: str
    income: float
    expense: float
    class_count: int
    active_students: int
    new_students: int
    avg_price: float | None = None
    revenue_per_student: float | None = None
