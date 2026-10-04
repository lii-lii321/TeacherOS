from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Payment
from app.routers.students import get_student_or_404
from app.schemas.business import BusinessSummaryOut, PaymentCreate, PaymentOut
from app.services import business_service

router = APIRouter(tags=["business"])


@router.post("/payments", response_model=PaymentOut, status_code=201)
async def create_payment(payload: PaymentCreate, db: AsyncSession = Depends(get_db)):
    await get_student_or_404(db, payload.student_id)
    payment = Payment(**payload.model_dump())
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.get("/payments", response_model=list[PaymentOut])
async def list_payments(student_id: int | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Payment).order_by(Payment.id.desc())
    if student_id is not None:
        query = query.where(Payment.student_id == student_id)
    return list((await db.execute(query)).scalars().all())


@router.get("/business/summary", response_model=BusinessSummaryOut)
async def business_summary(month: str | None = None, db: AsyncSession = Depends(get_db)):
    try:
        data = await business_service.summary(db, month)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return BusinessSummaryOut(**data)
