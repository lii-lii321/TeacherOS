from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Student
from app.schemas.students import StudentCreate, StudentOut, StudentProfileOut, StudentUpdate
from app.services import mastery_service, trend_service

router = APIRouter(prefix="/students", tags=["students"])


async def get_student_or_404(db: AsyncSession, student_id: int) -> Student:
    student = await db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="student not found")
    return student


@router.post("", response_model=StudentOut, status_code=201)
async def create_student(payload: StudentCreate, db: AsyncSession = Depends(get_db)):
    student = Student(**payload.model_dump())
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


@router.get("", response_model=list[StudentOut])
async def list_students(
    status: Literal["active", "archived", "all"] = "active", db: AsyncSession = Depends(get_db)
):
    query = select(Student).order_by(Student.id)
    if status != "all":
        query = query.where(Student.status == status)
    return list((await db.execute(query)).scalars().all())


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(student_id: int, db: AsyncSession = Depends(get_db)):
    return await get_student_or_404(db, student_id)


@router.patch("/{student_id}", response_model=StudentOut)
async def update_student(student_id: int, payload: StudentUpdate, db: AsyncSession = Depends(get_db)):
    student = await get_student_or_404(db, student_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    await db.commit()
    await db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=204)
async def archive_student(student_id: int, db: AsyncSession = Depends(get_db)):
    student = await get_student_or_404(db, student_id)
    student.status = "archived"
    await db.commit()


@router.get("/{student_id}/profile", response_model=StudentProfileOut)
async def student_profile(student_id: int, db: AsyncSession = Depends(get_db)):
    student = await get_student_or_404(db, student_id)
    return await mastery_service.build_profile(db, student)


@router.get("/{student_id}/trends")
async def student_trends(student_id: int, db: AsyncSession = Depends(get_db)):
    student = await get_student_or_404(db, student_id)
    return await trend_service.build_trends(db, student)
