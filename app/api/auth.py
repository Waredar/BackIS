from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_session
from app.db.models import User, Role, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role_name: str = "master"

class Token(BaseModel):
    access_token: str
    token_type: str

class UserOut(BaseModel):
    userid: int
    username: str
    email: str
    fullname: str
    isactive: bool


@router.post("/register", response_model=UserOut)
async def register(user_data: UserRegister, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.username == user_data.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    result = await session.execute(select(Role).where(Role.rolename == user_data.role_name))
    role = result.scalars().first()
    if not role:
        raise HTTPException(status_code=400, detail="Role not found")
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashedpassword=get_password_hash(user_data.password),
        fullname=user_data.full_name,
        isactive=True
    )
    session.add(new_user)
    await session.flush()
    
    user_role = UserRole(userid=new_user.userid, roleid=role.roleid)
    session.add(user_role)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.hashedpassword):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
