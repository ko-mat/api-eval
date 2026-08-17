from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import get_db
from app.models.user import User
from app.routes.deps import get_current_user
from app.utils.auth import verify_password, hash_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str = Field(..., examples=["admin"])
    password: str = Field(..., examples=["AdminPass2026!"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool

@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates user with username & password and returns a signed JWT access token.
    """
    stmt = select(User).filter(User.username == req.username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
        role=user.role
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Returns profile information of the currently authenticated user.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active
    )
