from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from app.db.session import get_session
from app.db.models import Payment, Appointment
from app.core.deps import require_role

router = APIRouter(prefix="/payments", tags=["payments"])

class PaymentCreate(BaseModel):
    appointmentid: int
    amount: float
    discounttotal: float = 0
    amountpaid: float
    paymentmethod: str = "Cash"
    paymentstatus: str = "Paid"

class PaymentOut(BaseModel):
    paymentid: int
    appointmentid: int
    paymentdatetime: datetime
    amount: float
    discounttotal: float
    amountpaid: float
    paymentmethod: str
    paymentstatus: str

@router.post("", response_model=PaymentOut, dependencies=[Depends(require_role("admin"))])
async def create_payment(
    payment_data: PaymentCreate,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Appointment).where(Appointment.appointmentid == payment_data.appointmentid)
    )
    appointment = result.scalars().first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    new_payment = Payment(**payment_data.model_dump())
    session.add(new_payment)
    
    appointment.status = "Completed"
    
    await session.commit()
    await session.refresh(new_payment)
    return new_payment
