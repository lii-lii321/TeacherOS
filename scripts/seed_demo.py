import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.models  # noqa: E402, F401
from app.database import Base, engine
from app.models import KnowledgePoint, Payment, Student
from app.services.copilot_service import process_lesson_note
from sqlalchemy.ext.asyncio import async_sessionmaker

STUDENTS = [
    {"name": "张同学", "grade": "初二", "subject": "数学", "current_score": 80, "target_score": 110},
    {"name": "李同学", "grade": "初三", "subject": "物理", "current_score": 65, "target_score": 85},
    {"name": "王同学", "grade": "高二", "subject": "英语", "current_score": 95, "target_score": 120},
]

ZHANG_KPS = [("一次函数", 72), ("几何证明", 41), ("二次函数", 58)]

NOTE = "今天讲了二次函数，学生对顶点式理解一般，做了10道题错了3道"


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        zhang, li, wang = (Student(**s) for s in STUDENTS)
        db.add_all([zhang, li, wang])
        await db.flush()

        for kp_name, mastery in ZHANG_KPS:
            db.add(KnowledgePoint(student_id=zhang.id, name=kp_name, mastery=mastery))

        db.add(Payment(student_id=zhang.id, amount=1600, kind="income", note="10月课酬"))
        db.add(Payment(student_id=li.id, amount=1200, kind="income", note="10月课酬"))
        db.add(Payment(student_id=zhang.id, amount=80, kind="expense", note="教材"))
        await db.commit()

        outcome = await process_lesson_note(db, zhang, NOTE)
        print(f"copilot: session #{outcome.session.id}, homework #{outcome.homework.id}")
        print("parent message:", outcome.parent_message)

    await engine.dispose()
    print("seed done -> teacheros.db")


if __name__ == "__main__":
    asyncio.run(main())
