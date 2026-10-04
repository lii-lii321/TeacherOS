from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ClassSession, Student
from app.routers.students import get_student_or_404
from app.schemas.classes import ClassSessionCreate, ClassSessionOut

router = APIRouter(prefix="/classes", tags=["classes"])


@router.post("", response_model=ClassSessionOut, status_code=201)
async def create_session(payload: ClassSessionCreate, db: AsyncSession = Depends(get_db)):
    await get_student_or_404(db, payload.student_id)
    data = payload.model_dump()
    session = ClassSession(**data)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("", response_model=list[ClassSessionOut])
async def list_sessions(student_id: int | None = None, db: AsyncSession = Depends(get_db)):
    query = select(ClassSession).order_by(ClassSession.id.desc())
    if student_id is not None:
        query = query.where(ClassSession.student_id == student_id)
    return list((await db.execute(query)).scalars().all())


@router.get("/{session_id}", response_model=ClassSessionOut)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    session = await db.get(ClassSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session
