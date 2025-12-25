from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_session
from app.db.models import Product
from app.core.deps import require_role

router = APIRouter(prefix="/products", tags=["products"])

class ProductCreate(BaseModel):
    productname: str
    category: Optional[str] = None
    unit: str
    unitprice: float
    stockquantity: int = 0
    isactive: bool = True

class ProductUpdate(BaseModel):
    productname: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    unitprice: Optional[float] = None
    stockquantity: Optional[int] = None
    isactive: Optional[bool] = None

class ProductOut(BaseModel):
    productid: int
    productname: str
    category: Optional[str]
    unit: str
    unitprice: float
    stockquantity: int
    isactive: bool

@router.get("", response_model=list[ProductOut], dependencies=[Depends(require_role("admin"))])
async def get_products(
    session: AsyncSession = Depends(get_session),
    active_only: bool = True
):
    query = select(Product)
    if active_only:
        query = query.where(Product.isactive == True)
    query = query.order_by(Product.category, Product.productname)
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_role("admin"))])
async def get_product(product_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Product).where(Product.productid == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("", response_model=ProductOut, dependencies=[Depends(require_role("admin"))])
async def create_product(
    product_data: ProductCreate,
    session: AsyncSession = Depends(get_session)
):
    new_product = Product(**product_data.model_dump())
    session.add(new_product)
    await session.commit()
    await session.refresh(new_product)
    return new_product

@router.put("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_role("admin"))])
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Product).where(Product.productid == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product_data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    
    await session.commit()
    await session.refresh(product)
    return product

@router.delete("/{product_id}", dependencies=[Depends(require_role("admin"))])
async def delete_product(product_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Product).where(Product.productid == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await session.delete(product)
    await session.commit()
    return {"status": "ok", "message": "Product deleted"}
