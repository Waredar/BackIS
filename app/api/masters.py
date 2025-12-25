# app/routers/masters.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import date

from app.db.session import get_session
from app.db.models import Master
from app.core.deps import require_role

router = APIRouter(prefix="/masters", tags=["masters"])

# --- Pydantic Models ---

class MasterCreate(BaseModel):
    fullname: str
    specialization: Optional[str] = None
    phone: str
    hiredate: date
    email: Optional[str] = None
    passport: Optional[str] = None
    address: Optional[str] = None
    birthdate: Optional[date] = None
    salary: Optional[float] = None
    commissionpercent: Optional[float] = 0.0
    paymenttype: str = "Monthly"
    isactive: bool = True

class MasterUpdate(BaseModel):
    fullname: Optional[str] = None
    specialization: Optional[str] = None
    phone: Optional[str] = None
    hiredate: Optional[date] = None
    email: Optional[str] = None
    address: Optional[str] = None
    salary: Optional[float] = None
    commissionpercent: Optional[float] = None
    isactive: Optional[bool] = None

class MasterOut(BaseModel):
    masterid: int
    fullname: str
    specialization: Optional[str] = None
    phone: str
    hiredate: date
    email: Optional[str] = None
    salary: Optional[float] = None
    isactive: bool

# --- Routes ---

@router.get("", response_model=list[MasterOut], dependencies=[Depends(require_role("admin"))])
async def get_masters(
    session: AsyncSession = Depends(get_session),
    active_only: bool = True
):
    query = select(Master)
    if active_only:
        query = query.where(Master.isactive == True)
    
    query = query.order_by(Master.fullname)
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/{master_id}", response_model=MasterOut, dependencies=[Depends(require_role("admin"))])
async def get_master(master_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Master).where(Master.masterid == master_id))
    master = result.scalars().first()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    return master

@router.post("", response_model=MasterOut, dependencies=[Depends(require_role("admin"))])
async def create_master(
    master_data: MasterCreate,
    session: AsyncSession = Depends(get_session)
):
    # Pydantic dump автоматически подставит поля, если их имена совпадают с моделью SQLAlchemy
    new_master = Master(**master_data.model_dump())
    
    session.add(new_master)
    await session.commit()
    await session.refresh(new_master)
    
    return new_master

@router.put("/{master_id}", response_model=MasterOut, dependencies=[Depends(require_role("admin"))])
async def update_master(
    master_id: int,
    master_data: MasterUpdate,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Master).where(Master.masterid == master_id))
    master = result.scalars().first()
    
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    
    for key, value in master_data.model_dump(exclude_unset=True).items():
        setattr(master, key, value)
    
    await session.commit()
    await session.refresh(master)
    
    return master

@router.delete("/{master_id}", dependencies=[Depends(require_role("admin"))])
async def delete_master(master_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Master).where(Master.masterid == master_id))
    master = result.scalars().first()
    
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    
    await session.delete(master)
    await session.commit()
    
    return {"status": "ok", "message": "Master deleted"}
