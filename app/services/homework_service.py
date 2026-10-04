from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Homework
from app.services import mastery_service
from app.utils.clock import utcnow


async def grade_homework(db: AsyncSession, homework: Homework, results) -> tuple[float, list]:
    accuracy, updates = await mastery_service.apply_grading(db, homework.student_id, homework.items, results)
    correct = sum(1 for r in results if r.correct)
    homework.graded = {
        "accuracy": accuracy,
        "correct": correct,
        "total": len(results),
        "graded_at": utcnow().isoformat(),
    }
    homework.status = "graded"
    await db.commit()
    return accuracy, updates
