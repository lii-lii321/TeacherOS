from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClassSession, Homework, MasteryLog, Student

IMPROVE_TOLERANCE = 0.05


async def build_trends(db: AsyncSession, student: Student) -> dict:
    student_id = student.id

    graded = (
        await db.scalars(
            select(Homework)
            .where(Homework.student_id == student_id, Homework.graded.isnot(None))
            .order_by(Homework.assigned_at)
        )
    ).all()
    accuracy_series = [
        {
            "date": hw.assigned_at.date().isoformat(),
            "accuracy": (hw.graded or {}).get("accuracy"),
            "homework_id": hw.id,
        }
        for hw in graded
    ]

    logs = (
        await db.scalars(
            select(MasteryLog)
            .where(MasteryLog.student_id == student_id, MasteryLog.id.is_not(None))
            .order_by(MasteryLog.created_at, MasteryLog.id)
            .limit(50)
        )
    ).all()
    mastery_logs = [
        {"date": log.created_at.date().isoformat(), "name": log.name, "mastery": log.mastery, "observed": log.observed}
        for log in logs
    ]

    sessions = (
        await db.scalars(
            select(ClassSession)
            .where(ClassSession.student_id == student_id, ClassSession.id.is_not(None))
            .order_by(ClassSession.occurred_at.desc())
            .limit(5)
        )
    ).all()
    recent_sessions = [
        {"date": s.occurred_at.date().isoformat(), "topic": s.topic, "performance": s.understanding}
        for s in reversed(sessions)
    ]

    direction = _accuracy_direction(accuracy_series)
    return {
        "accuracy_series": accuracy_series,
        "accuracy_direction": direction,
        "mastery_logs": mastery_logs,
        "recent_sessions": recent_sessions,
        "suggestion": _suggestion(direction, mastery_logs),
    }


def _accuracy_direction(series: list) -> str:
    if len(series) < 2:
        return "insufficient_data"
    half = len(series) // 2
    first = sum(point["accuracy"] for point in series[:half]) / half
    second = sum(point["accuracy"] for point in series[half:]) / (len(series) - half)
    delta = second - first
    if delta > IMPROVE_TOLERANCE:
        return "improving"
    if delta < -IMPROVE_TOLERANCE:
        return "declining"
    return "flat"


def _suggestion(direction: str, logs: list) -> str:
    if logs:
        latest = {}
        for log in logs:
            latest[log["name"]] = log["mastery"]
        weakest = min(latest, key=latest.get)
        weakest_line = f"重点关注「{weakest}」（最新掌握度 {latest[weakest]}%）"
    else:
        weakest_line = "先记录课程与作业积累学情"
    if direction == "declining":
        return f"正确率呈下降趋势，{weakest_line}，建议降低新知识节奏、先补基础"
    if direction == "improving":
        return f"正确率持续上升，{weakest_line}，可逐步加入综合题"
    return f"正确率基本平稳，{weakest_line}"
