from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClassSession, Payment, Student
from app.utils.clock import utcnow


def month_range(month: str | None) -> tuple[datetime, datetime, str]:
    if month:
        try:
            month_start = datetime.strptime(month, "%Y-%m")
        except ValueError as exc:
            raise ValueError("month must look like YYYY-MM") from exc
    else:
        now = utcnow()
        month_start = datetime(now.year, now.month, 1)
    if month_start.month == 12:
        next_start = datetime(month_start.year + 1, 1, 1)
    else:
        next_start = datetime(month_start.year, month_start.month + 1, 1)
    return month_start, next_start, month_start.strftime("%Y-%m")


async def summary(db: AsyncSession, month: str | None = None) -> dict:
    start, end, label = month_range(month)

    pays = (
        await db.execute(
            select(Payment).where(and_(Payment.occurred_at >= start, Payment.occurred_at < end))
        )
    ).scalars().all()
    income = round(sum(p.amount for p in pays if p.kind == "income"), 2)
    expense = round(sum(p.amount for p in pays if p.kind == "expense"), 2)

    class_count = (
        await db.scalar(
            select(func.count(ClassSession.id)).where(
                and_(ClassSession.occurred_at >= start, ClassSession.occurred_at < end)
            )
        )
    ) or 0

    active_ids = {p.student_id for p in pays}
    session_ids = (
        await db.scalars(
            select(ClassSession.student_id).where(
                and_(ClassSession.occurred_at >= start, ClassSession.occurred_at < end)
            )
        )
    ).all()
    active_ids.update(session_ids)

    new_students = (
        await db.scalar(
            select(func.count(Student.id)).where(
                and_(Student.created_at >= start, Student.created_at < end)
            )
        )
    ) or 0

    return {
        "month": label,
        "income": income,
        "expense": expense,
        "class_count": class_count,
        "active_students": len(active_ids),
        "new_students": new_students,
        "avg_price": round(income / class_count, 2) if class_count else None,
        "revenue_per_student": round(income / len(active_ids), 2) if active_ids else None,
    }
