from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from datetime import date
from typing import Optional, List
from app.db.session import get_session
from app.db.models import Payment
from app.core.deps import require_role

router = APIRouter(prefix="/reports", tags=["reports"])

class RevenueReport(BaseModel):
    date: date
    total_revenue: float
    total_transactions: int

@router.get("/revenue", response_model=List[RevenueReport], dependencies=[Depends(require_role("admin"))])
async def get_revenue_report(
    session: AsyncSession = Depends(get_session),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
):
    query = select(
        func.date(Payment.paymentdatetime).label('date'),
        func.sum(Payment.amountpaid).label('total_revenue'),
        func.count(Payment.paymentid).label('total_transactions')
    ).where(Payment.paymentstatus == 'Paid')
    
    if date_from:
        query = query.where(func.date(Payment.paymentdatetime) >= date_from)
    if date_to:
        query = query.where(func.date(Payment.paymentdatetime) <= date_to)
    
    query = query.group_by(func.date(Payment.paymentdatetime)).order_by(func.date(Payment.paymentdatetime).desc())
    
    result = await session.execute(query)
    return [{"date": row[0], "total_revenue": float(row[1]), "total_transactions": row[2]} for row in result]
