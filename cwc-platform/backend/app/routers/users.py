from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get the current user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile."""
    if update_data.name is not None:
        current_user.name = update_data.name
    if update_data.avatar_url is not None:
        current_user.avatar_url = update_data.avatar_url

    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)
