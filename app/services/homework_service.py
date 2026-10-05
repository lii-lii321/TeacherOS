import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Homework
from app.services import mastery_service
from app.utils.clock import utcnow


def _normalize(text: str) -> str:
    return re.sub(r"[\s，。,．.；;：:、'\"（）()]+", "", str(text)).lower()


def _last_number(text: str) -> float | None:
    numbers = re.findall(r"-?\d+(?:\.\d+)?", text)
    return float(numbers[-1]) if numbers else None


def check_answer(given: str, expected: str) -> bool:
    """Normalized string equality, falling back to numeric comparison of the
    last number in each answer (so "x=3" and "3" both match)."""
    if given is None or expected is None:
        return False
    normalized_given, normalized_expected = _normalize(given), _normalize(expected)
    if not normalized_given or not normalized_expected:
        return False
    if normalized_given == normalized_expected:
        return True
    given_number, expected_number = _last_number(normalized_given), _last_number(normalized_expected)
    if given_number is None or expected_number is None:
        return False
    return abs(given_number - expected_number) < 1e-9


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
