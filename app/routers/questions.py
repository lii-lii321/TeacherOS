from fastapi import APIRouter

from app.services import question_bank

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("")
async def get_questions(knowledge_point: str | None = None, difficulty: str | None = None):
    return question_bank.list_questions(knowledge_point, difficulty)
