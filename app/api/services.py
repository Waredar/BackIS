from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_session
from app.db.models import Service
from app.core.deps import require_role

router = APIRouter(prefix="/services", tags=["services"])

class ServiceCreate(BaseModel):
    servicename: str
    description: Optional[str] = None
    category: Optional[str] = None
    durationminutes: int
    baseprice: float
    isactive: bool = True

class ServiceUpdate(BaseModel):
    servicename: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    durationminutes: Optional[int] = None
    baseprice: Optional[float] = None
    isactive: Optional[bool] = None

class ServiceOut(BaseModel):
    serviceid: int
    servicename: str
    description: Optional[str]
    category: Optional[str]
    durationminutes: int
    baseprice: float
    isactive: bool

@router.get("", response_model=list[ServiceOut])
async def get_services(
    session: AsyncSession = Depends(get_session),
    active_only: bool = True
):
    query = select(Service)
    if active_only:
        query = query.where(Service.isactive == True)
    query = query.order_by(Service.category, Service.servicename)
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/{service_id}", response_model=ServiceOut, dependencies=[Depends(require_role("admin"))])
async def get_service(service_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Service).where(Service.serviceid == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@router.post("", response_model=ServiceOut, dependencies=[Depends(require_role("admin"))])
async def create_service(
    service_data: ServiceCreate,
    session: AsyncSession = Depends(get_session)
):
    new_service = Service(**service_data.model_dump())
    session.add(new_service)
    await session.commit()
    await session.refresh(new_service)
    return new_service

@router.put("/{service_id}", response_model=ServiceOut, dependencies=[Depends(require_role("admin"))])
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Service).where(Service.serviceid == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    for key, value in service_data.model_dump(exclude_unset=True).items():
        setattr(service, key, value)
    
    await session.commit()
    await session.refresh(service)
    return service

@router.delete("/{service_id}", dependencies=[Depends(require_role("admin"))])
async def delete_service(service_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Service).where(Service.serviceid == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    await session.delete(service)
    await session.commit()
    return {"status": "ok", "message": "Service deleted"}
