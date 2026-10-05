from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Homework
from app.routers.students import get_student_or_404
from app.schemas.homework import GradeOut, HomeworkCreate, HomeworkOut, SubmitAnswers, SubmitItem, SubmitResults
from app.services import homework_service

router = APIRouter(prefix="/homework", tags=["homework"])


@router.post("", response_model=HomeworkOut, status_code=201)
async def create_homework(payload: HomeworkCreate, db: AsyncSession = Depends(get_db)):
    await get_student_or_404(db, payload.student_id)
    items = []
    for i, item in enumerate(payload.items, start=1):
        items.append({"id": i, "knowledge_point": item.knowledge_point, "difficulty": item.difficulty, "question": item.question})
    homework = Homework(student_id=payload.student_id, title=payload.title, items=items)
    db.add(homework)
    await db.commit()
    await db.refresh(homework)
    return homework


@router.get("", response_model=list[HomeworkOut])
async def list_homework(student_id: int | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Homework).order_by(Homework.id.desc())
    if student_id is not None:
        query = query.where(Homework.student_id == student_id)
    return list((await db.execute(query)).scalars().all())


@router.get("/{homework_id}", response_model=HomeworkOut)
async def get_homework(homework_id: int, db: AsyncSession = Depends(get_db)):
    homework = await db.get(Homework, homework_id)
    if homework is None:
        raise HTTPException(status_code=404, detail="homework not found")
    return homework


@router.post("/{homework_id}/submit", response_model=GradeOut)
async def submit_homework(homework_id: int, payload: SubmitResults, db: AsyncSession = Depends(get_db)):
    homework = await db.get(Homework, homework_id)
    if homework is None:
        raise HTTPException(status_code=404, detail="homework not found")
    valid_ids = {it["id"] for it in (homework.items or []) if isinstance(it, dict)}
    seen: set[int] = set()
    for r in payload.results:
        if r.item_id not in valid_ids or r.item_id in seen:
            raise HTTPException(status_code=422, detail="results contain unknown or duplicate item_id")
        seen.add(r.item_id)
    accuracy, updates = await homework_service.grade_homework(db, homework, payload.results)
    return GradeOut(
        homework_id=homework.id,
        accuracy=accuracy,
        knowledge_updates=[{"name": kp.name, "mastery": kp.mastery} for kp in updates],
    )


@router.post("/{homework_id}/submit-answers", response_model=GradeOut)
async def submit_answers(homework_id: int, payload: SubmitAnswers, db: AsyncSession = Depends(get_db)):
    homework = await db.get(Homework, homework_id)
    if homework is None:
        raise HTTPException(status_code=404, detail="homework not found")
    items = homework.items or []
    if any(not isinstance(item, dict) or not item.get("answer") for item in items):
        raise HTTPException(status_code=409, detail="homework has no answer key; use /submit with manual results")
    if len(payload.answers) != len(items):
        raise HTTPException(status_code=422, detail=f"expected {len(items)} answers, got {len(payload.answers)}")

    results = [
        SubmitItem(item_id=int(item["id"]), correct=homework_service.check_answer(payload.answers[index], item["answer"]))
        for index, item in enumerate(items)
    ]
    accuracy, updates = await homework_service.grade_homework(db, homework, results)
    return GradeOut(
        homework_id=homework.id,
        accuracy=accuracy,
        knowledge_updates=[{"name": kp.name, "mastery": kp.mastery} for kp in updates],
    )
