from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.db.session import get_session
from app.db.models import Client
from app.core.deps import require_role


router = APIRouter(prefix="/clients", tags=["clients"])


class ClientCreate(BaseModel):
    fullname: str
    phone: str
    email: Optional[str] = None
    birthdate: Optional[date] = None
    loyaltystatus: str = "Basic"
    notes: Optional[str] = None


class ClientOut(BaseModel):
    clientid: int
    fullname: str
    phone: str
    email: Optional[str]
    birthdate: Optional[date]
    loyaltystatus: str
    notes: Optional[str]


class ClientList(BaseModel):
    total: int
    items: list[ClientOut]


class ClientUpdate(BaseModel):
    fullname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    birthdate: Optional[date] = None
    loyaltystatus: Optional[str] = None
    notes: Optional[str] = None


@router.get("", response_model=ClientList, dependencies=[Depends(require_role("admin"))])
async def get_clients(
    session: AsyncSession = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    loyaltystatus: Optional[str] = None,
    sort_by: Optional[str] = Query(None),
    sort_order: Optional[str] = Query('asc', regex='^(asc|desc)$')
):
    query = select(Client)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Client.fullname.ilike(search_pattern)) |
            (Client.phone.ilike(search_pattern)) |
            (Client.email.ilike(search_pattern))
        )
    
    if loyaltystatus:
        query = query.where(Client.loyaltystatus == loyaltystatus)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()
    
    # Применение сортировки
    if sort_by:
        column = getattr(Client, sort_by, None)
        if column is not None:
            if sort_order == 'desc':
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        else:
            query = query.order_by(Client.clientid.desc())
    else:
        query = query.order_by(Client.clientid.desc())
    
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    clients = result.scalars().all()
    
    return {"total": total, "items": clients}


@router.post("", response_model=ClientOut, dependencies=[Depends(require_role("admin"))])
async def create_client(
    client_data: ClientCreate,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Client).where(Client.phone == client_data.phone))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Phone already exists")
    
    new_client = Client(**client_data.model_dump())
    session.add(new_client)
    await session.commit()
    await session.refresh(new_client)
    return new_client


@router.get("/{client_id}", response_model=ClientOut, dependencies=[Depends(require_role("admin"))])
async def get_client(client_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Client).where(Client.clientid == client_id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.put("/{client_id}", response_model=ClientOut, dependencies=[Depends(require_role("admin"))])
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Client).where(Client.clientid == client_id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    for key, value in client_data.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    
    await session.commit()
    await session.refresh(client)
    return client


@router.delete("/{client_id}", dependencies=[Depends(require_role("admin"))])
async def delete_client(client_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Client).where(Client.clientid == client_id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    await session.delete(client)
    await session.commit()
    return {"status": "ok", "message": "Client deleted"}
