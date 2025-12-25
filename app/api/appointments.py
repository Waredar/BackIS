# app/routers/appointments.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

from app.db.session import get_session
from app.db.models import Appointment, Client, Master, Service, AppointmentService, DimDate, User
from app.core.deps import require_role, get_current_user

router = APIRouter(prefix="/appointments", tags=["appointments"])

# --- Pydantic Models ---

class AppointmentCreate(BaseModel):
    clientid: int
    masterid: int
    startdatetime: datetime
    enddatetime: Optional[datetime] = None
    source: str = "Phone"
    status: str = "Planned"

class ServiceInAppointment(BaseModel):
    serviceid: int
    quantity: int = 1
    priceatvisit: float
    discountamount: float = 0

class AppointmentOut(BaseModel):
    appointmentid: int
    clientid: int
    masterid: int
    dateid: int
    startdatetime: datetime
    enddatetime: Optional[datetime]
    status: str
    source: str

class AppointmentDetail(AppointmentOut):
    client_name: Optional[str] = None
    master_name: Optional[str] = None

# --- Routes ---

@router.post("", response_model=AppointmentOut, dependencies=[Depends(require_role("admin"))])
async def create_appointment(
    appointment_data: AppointmentCreate,
    session: AsyncSession = Depends(get_session)
):
    # 1. Проверки существования
    client_exists = await session.execute(select(Client).where(Client.clientid == appointment_data.clientid))
    if not client_exists.scalars().first():
        raise HTTPException(status_code=404, detail="Client not found")

    master_exists = await session.execute(select(Master).where(Master.masterid == appointment_data.masterid))
    if not master_exists.scalars().first():
        raise HTTPException(status_code=404, detail="Master not found")

    # 2. ПОИСК DateID (Критически важная часть для новой БД)
    visit_date = appointment_data.startdatetime.date()
    date_query = await session.execute(select(DimDate.dateid).where(DimDate.fulldate == visit_date))
    date_id = date_query.scalars().first()

    if not date_id:
        raise HTTPException(
            status_code=400, 
            detail=f"Calendar date {visit_date} not initialized in DimDate. Please run fill_dim_date SQL function."
        )

    # 3. Создание записи
    new_appointment = Appointment(
        clientid=appointment_data.clientid,
        masterid=appointment_data.masterid,
        dateid=date_id,  # Присваиваем найденный ID
        startdatetime=appointment_data.startdatetime,
        enddatetime=appointment_data.enddatetime,
        source=appointment_data.source,
        status=appointment_data.status
    )
    
    session.add(new_appointment)
    await session.commit()
    await session.refresh(new_appointment)
    
    return new_appointment

@router.post("/{appointment_id}/services", dependencies=[Depends(require_role("admin"))])
async def add_services_to_appointment(
    appointment_id: int,
    services: List[ServiceInAppointment],
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Appointment).where(Appointment.appointmentid == appointment_id))
    appointment = result.scalars().first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    count = 0
    for svc in services:
        # Проверяем услугу
        s_res = await session.execute(select(Service).where(Service.serviceid == svc.serviceid))
        if not s_res.scalars().first():
             continue # Или raise error

        app_service = AppointmentService(
            appointmentid=appointment_id,
            serviceid=svc.serviceid,
            quantity=svc.quantity,
            priceatvisit=svc.priceatvisit,
            discountamount=svc.discountamount
        )
        session.add(app_service)
        count += 1
    
    await session.commit()
    return {"status": "ok", "added": count}

@router.get("", response_model=List[AppointmentDetail], dependencies=[Depends(require_role("admin"))])
async def get_appointments(
    session: AsyncSession = Depends(get_session),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    masterid: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500)
):
    query = select(Appointment, Client.fullname, Master.fullname).join(
        Client, Client.clientid == Appointment.clientid
    ).join(
        Master, Master.masterid == Appointment.masterid
    )

    if date_from:
        query = query.where(func.date(Appointment.startdatetime) >= date_from)
    if date_to:
        query = query.where(func.date(Appointment.startdatetime) <= date_to)
    if masterid:
        query = query.where(Appointment.masterid == masterid)
    if status:
        query = query.where(Appointment.status == status)

    query = query.order_by(Appointment.startdatetime.desc()).limit(limit)
    
    result = await session.execute(query)
    
    appointments = []
    for row in result:
        appt_obj = row[0]
        appointments.append({
            "appointmentid": appt_obj.appointmentid,
            "clientid": appt_obj.clientid,
            "masterid": appt_obj.masterid,
            "dateid": appt_obj.dateid,
            "startdatetime": appt_obj.startdatetime,
            "enddatetime": appt_obj.enddatetime,
            "status": appt_obj.status,
            "source": appt_obj.source,
            "client_name": row[1],
            "master_name": row[2]
        })
    
    return appointments

@router.put("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: int,
    status: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await session.execute(select(Appointment).where(Appointment.appointmentid == appointment_id))
    appointment = result.scalars().first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    appointment.status = status
    appointment.updatedat = datetime.now()
    
    await session.commit()
    return {"status": "ok", "new_status": status}
