"""Public testimonial routes for recording and gallery."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.services.cloudinary_service import cloudinary_service
from app.models.testimonial import Testimonial
from app.schemas.testimonial import (
    TestimonialRequestInfo,
    TestimonialSubmit,
    TestimonialSubmitResponse,
    TestimonialPublic,
    TestimonialGallery,
    VideoUploadSignature,
    VideoUploadResponse,
)

router = APIRouter(prefix="/api", tags=["Testimonial Public"])


# Public gallery endpoint
@router.get("/testimonials/public", response_model=TestimonialGallery)
async def get_public_testimonials(
    organization_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get approved testimonials for public gallery."""
    query = select(Testimonial).where(
        Testimonial.status == "approved",
        Testimonial.permission_granted == True,
    )

    if organization_id:
        query = query.where(Testimonial.organization_id == organization_id)

    # Get featured testimonials
    featured_query = query.where(Testimonial.featured == True).order_by(
        Testimonial.display_order
    )
    featured_result = await db.execute(featured_query)
    featured = featured_result.scalars().all()

    # Get non-featured testimonials
    items_query = query.where(Testimonial.featured == False).order_by(
        Testimonial.display_order,
        Testimonial.submitted_at.desc(),
    )
    items_result = await db.execute(items_query)
    items = items_result.scalars().all()

    def to_public(t: Testimonial) -> TestimonialPublic:
        return TestimonialPublic(
            id=t.id,
            author_name=t.author_name,
            author_title=t.author_title,
            author_company=t.author_company,
            author_photo_url=t.author_photo_url,
            quote=t.quote,
            video_url=t.video_url,
            thumbnail_url=t.thumbnail_url,
            video_duration_seconds=t.video_duration_seconds,
            featured=t.featured,
        )

    return TestimonialGallery(
        featured=[to_public(t) for t in featured],
        items=[to_public(t) for t in items],
        total=len(featured) + len(items),
    )


# Token-based public endpoints
@router.get("/testimonial/{token}", response_model=TestimonialRequestInfo)
async def get_testimonial_request(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Get testimonial request info by token."""
    result = await db.execute(
        select(Testimonial).where(Testimonial.request_token == token)
    )
    testimonial = result.scalar_one_or_none()

    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial request not found",
        )

    return TestimonialRequestInfo(
        id=testimonial.id,
        author_name=testimonial.author_name,
        author_title=testimonial.author_title,
        author_company=testimonial.author_company,
        status=testimonial.status,
        already_submitted=testimonial.submitted_at is not None,
    )


@router.post("/testimonial/{token}", response_model=TestimonialSubmitResponse)
async def submit_testimonial(
    token: str,
    data: TestimonialSubmit,
    db: AsyncSession = Depends(get_db),
):
    """Submit a testimonial."""
    result = await db.execute(
        select(Testimonial).where(Testimonial.request_token == token)
    )
    testimonial = result.scalar_one_or_none()

    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial request not found",
        )

    if testimonial.submitted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Testimonial has already been submitted",
        )

    # Update testimonial with submission data
    testimonial.author_name = data.author_name
    testimonial.author_title = data.author_title
    testimonial.author_company = data.author_company
    testimonial.author_photo_url = data.author_photo_url
    testimonial.quote = data.quote
    testimonial.video_url = data.video_url
    testimonial.video_public_id = data.video_public_id
    testimonial.video_duration_seconds = data.video_duration_seconds
    testimonial.thumbnail_url = data.thumbnail_url
    testimonial.permission_granted = data.permission_granted
    testimonial.submitted_at = datetime.utcnow()

    await db.commit()

    return TestimonialSubmitResponse(
        id=testimonial.id,
        message="Thank you for sharing your testimonial!",
    )


# Video upload endpoints
@router.get("/upload/video/signature", response_model=VideoUploadSignature)
async def get_upload_signature():
    """Get Cloudinary upload signature for direct browser uploads."""
    signature_data = cloudinary_service.generate_upload_signature()
    return VideoUploadSignature(**signature_data)


@router.post("/upload/video", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
):
    """Upload a video file to Cloudinary."""
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a video",
        )

    # Read file content
    content = await file.read()

    # Check file size (100MB max)
    if len(content) > 104857600:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video file too large (max 100MB)",
        )

    try:
        result = cloudinary_service.upload_video(
            file_data=content,
            filename=file.filename or "video.webm",
        )

        return VideoUploadResponse(
            url=result["url"],
            public_id=result["public_id"],
            duration=result["duration"],
            thumbnail_url=result.get("thumbnail_url"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload video: {str(e)}",
        )
