"""Auth routes — register, login, and current-user retrieval."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, hash_password, verify_password
from app.db.models import Farmer
from app.db.postgres import get_db
from app.dependencies import get_current_user
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user account (farmer, shop_owner, or extension_officer)."""
    result = await db.execute(select(Farmer).where(Farmer.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    farmer = Farmer(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        district=body.district,
    )
    db.add(farmer)
    await db.commit()
    await db.refresh(farmer)
    return farmer


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and return a JWT Bearer token."""
    result = await db.execute(select(Farmer).where(Farmer.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"access_token": token}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Farmer = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user
