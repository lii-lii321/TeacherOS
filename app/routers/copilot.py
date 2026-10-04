from fastapi import APIRouter, Depends

from app.database import get_db
from app.routers.students import get_student_or_404
from app.schemas.copilot import CopilotResultOut, LessonNoteIn
from app.services import copilot_service

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/lesson-note", response_model=CopilotResultOut)
async def lesson_note(payload: LessonNoteIn, db=Depends(get_db)):
    student = await get_student_or_404(db, payload.student_id)
    outcome = await copilot_service.process_lesson_note(
        db, student, payload.note, create_records=payload.create_records
    )
    return CopilotResultOut(
        structured=outcome.structured,
        parent_message=outcome.parent_message,
        homework_estimated_minutes=(outcome.structured.get("homework") or {}).get("estimated_minutes", 0),
        session=outcome.session,
        homework=outcome.homework,
    )
