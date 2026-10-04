from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClassSession, Homework, KnowledgePoint, Student
from app.utils.clock import utcnow

WEAK_THRESHOLD = 70


async def upsert_kp(db: AsyncSession, student_id: int, name: str, mastery: int | None = None) -> KnowledgePoint:
    result = await db.execute(
        select(KnowledgePoint).where(KnowledgePoint.student_id == student_id, KnowledgePoint.name == name)
    )
    kp = result.scalar_one_or_none()
    if kp is None:
        kp = KnowledgePoint(student_id=student_id, name=name, mastery=50 if mastery is None else mastery)
        db.add(kp)
    elif mastery is not None:
        kp.mastery = mastery
    await db.flush()
    return kp


async def apply_grading(db: AsyncSession, student_id: int, items: list[dict], results) -> tuple[float, list[KnowledgePoint]]:
    item_map = {it["id"]: it for it in items if isinstance(it, dict)}
    per_kp: dict[str, list[bool]] = {}
    for r in results:
        item = item_map.get(r.item_id)
        if item is None:
            continue
        per_kp.setdefault(item["knowledge_point"], []).append(r.correct)

    updates: list[KnowledgePoint] = []
    for kp_name, marks in per_kp.items():
        kp = await upsert_kp(db, student_id, kp_name)
        observed = round(100 * sum(1 for m in marks if m) / len(marks))
        kp.mastery = int(round(kp.mastery * 0.7 + observed * 0.3))
        updates.append(kp)

    accuracy = round(sum(1 for r in results if r.correct) / len(results), 4) if results else 0.0
    return accuracy, updates


async def build_profile(db: AsyncSession, student: Student) -> dict:
    kps = (
        await db.execute(
            select(KnowledgePoint)
            .where(KnowledgePoint.student_id == student.id)
            .order_by(KnowledgePoint.mastery.asc())
        )
    ).scalars().all()

    homework_count = await db.scalar(select(func.count(Homework.id)).where(Homework.student_id == student.id)) or 0
    session_count = await db.scalar(select(func.count(ClassSession.id)).where(ClassSession.student_id == student.id)) or 0

    last_graded = (
        await db.execute(
            select(Homework)
            .where(Homework.student_id == student.id, Homework.graded.isnot(None))
            .order_by(Homework.assigned_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    return {
        "student": student,
        "knowledge_points": kps,
        "weak_points": [kp.name for kp in kps[:3] if kp.mastery < WEAK_THRESHOLD],
        "recent_accuracy": (last_graded.graded or {}).get("accuracy") if last_graded else None,
        "homework_count": homework_count,
        "session_count": session_count,
    }


def next_review_suggestion(kps: list[KnowledgePoint]) -> str:
    if not kps:
        return "暂无学情数据，先记录一节课或批改一次作业"
    weakest = kps[0]
    return f"优先复习「{weakest.name}」（掌握度 {weakest.mastery}%），建议下周安排 2 道综合题"
