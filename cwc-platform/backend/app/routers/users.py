from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.brand_color_service import brand_color_service
from app.services.cloudinary_service import cloudinary_service
from app.models.user import User
from app.schemas.user import UserImageUploadResponse, UserResponse, UserUpdate

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
    if update_data.booking_page_title is not None:
        current_user.booking_page_title = update_data.booking_page_title
    if update_data.booking_page_description is not None:
        current_user.booking_page_description = update_data.booking_page_description
    if update_data.booking_page_brand_color is not None:
        current_user.booking_page_brand_color = update_data.booking_page_brand_color
    if update_data.booking_page_logo_url is not None:
        current_user.booking_page_logo_url = update_data.booking_page_logo_url
    if update_data.booking_page_banner_url is not None:
        current_user.booking_page_banner_url = update_data.booking_page_banner_url

    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.post("/me/upload-image", response_model=UserImageUploadResponse)
async def upload_current_user_image(
    target: Literal["avatar", "booking_logo", "booking_banner"],
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload an image for the current user's profile or booking page branding."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file too large (max 10MB)",
        )

    upload = cloudinary_service.upload_image(
        file_data=content,
        filename=file.filename or "branding-image.png",
        folder="branding",
        content_type=file.content_type,
    )

    suggested_colors: list[str] = []
    if target == "avatar":
        current_user.avatar_url = upload["url"]
    elif target == "booking_logo":
        current_user.booking_page_logo_url = upload["url"]
        suggested_colors = brand_color_service.extract_palette(
            content,
            fallback=current_user.booking_page_brand_color or "#2A7B8C",
        )
    else:
        current_user.booking_page_banner_url = upload["url"]

    await db.commit()
    await db.refresh(current_user)
    return UserImageUploadResponse(
        user=UserResponse.model_validate(current_user),
        suggested_colors=suggested_colors,
    )
