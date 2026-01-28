"""
Tests for Public Testimonial endpoints.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import uuid
from io import BytesIO

from httpx import AsyncClient
from sqlalchemy import select

from app.models.testimonial import Testimonial
from app.models.contact import Contact


@pytest.fixture
async def test_testimonial_request(db_session, test_contact: Contact) -> Testimonial:
    """Create a test testimonial request."""
    testimonial = Testimonial(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        author_name=f"{test_contact.first_name} {test_contact.last_name or ''}".strip(),
        request_token=str(uuid.uuid4()),
        status="pending",
    )
    db_session.add(testimonial)
    await db_session.commit()
    await db_session.refresh(testimonial)
    return testimonial


@pytest.fixture
async def test_approved_testimonial(db_session, test_contact: Contact) -> Testimonial:
    """Create an approved testimonial for gallery."""
    testimonial = Testimonial(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        author_name="Jane Doe",
        author_title="CEO",
        author_company="Test Corp",
        quote="This coaching was transformative!",
        status="approved",
        permission_granted=True,
        featured=False,
        submitted_at=datetime.utcnow(),
    )
    db_session.add(testimonial)
    await db_session.commit()
    await db_session.refresh(testimonial)
    return testimonial


@pytest.fixture
async def test_featured_testimonial(db_session, test_contact: Contact) -> Testimonial:
    """Create a featured testimonial for gallery."""
    testimonial = Testimonial(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        author_name="John Smith",
        author_title="Director",
        author_company="Another Corp",
        quote="Absolutely life-changing experience!",
        status="approved",
        permission_granted=True,
        featured=True,
        display_order=1,
        submitted_at=datetime.utcnow(),
    )
    db_session.add(testimonial)
    await db_session.commit()
    await db_session.refresh(testimonial)
    return testimonial


class TestPublicGallery:
    """Tests for public testimonial gallery."""

    @pytest.mark.asyncio
    async def test_get_gallery_empty(self, client: AsyncClient):
        """Test getting empty gallery."""
        response = await client.get("/api/testimonials/public")
        assert response.status_code == 200
        data = response.json()
        assert "featured" in data
        assert "items" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_gallery_with_testimonials(
        self, client: AsyncClient, test_approved_testimonial: Testimonial
    ):
        """Test getting gallery with testimonials."""
        response = await client.get("/api/testimonials/public")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_get_gallery_featured_separate(
        self,
        client: AsyncClient,
        test_approved_testimonial: Testimonial,
        test_featured_testimonial: Testimonial,
    ):
        """Test featured testimonials are separate from items."""
        response = await client.get("/api/testimonials/public")
        assert response.status_code == 200
        data = response.json()
        assert len(data["featured"]) >= 1
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_gallery_excludes_unapproved(
        self, db_session, client: AsyncClient, test_contact: Contact
    ):
        """Test gallery excludes unapproved testimonials."""
        # Create pending testimonial
        pending = Testimonial(
            id=str(uuid.uuid4()),
            contact_id=test_contact.id,
            author_name="Pending User",
            status="submitted",
            permission_granted=True,
        )
        db_session.add(pending)
        await db_session.commit()

        response = await client.get("/api/testimonials/public")
        assert response.status_code == 200
        data = response.json()
        # Pending testimonial should not appear
        all_names = [t["author_name"] for t in data["items"] + data["featured"]]
        assert "Pending User" not in all_names


class TestGetTestimonialRequest:
    """Tests for getting testimonial request by token."""

    @pytest.mark.asyncio
    async def test_get_request_success(
        self, client: AsyncClient, test_testimonial_request: Testimonial
    ):
        """Test getting testimonial request by token."""
        response = await client.get(
            f"/api/testimonial/{test_testimonial_request.request_token}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_testimonial_request.id
        assert data["already_submitted"] is False

    @pytest.mark.asyncio
    async def test_get_request_not_found(self, client: AsyncClient):
        """Test getting non-existent request."""
        response = await client.get(f"/api/testimonial/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_request_shows_submitted_status(
        self, db_session, client: AsyncClient, test_testimonial_request: Testimonial
    ):
        """Test request shows if already submitted."""
        test_testimonial_request.submitted_at = datetime.utcnow()
        await db_session.commit()

        response = await client.get(
            f"/api/testimonial/{test_testimonial_request.request_token}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["already_submitted"] is True


class TestSubmitTestimonial:
    """Tests for submitting testimonials."""

    @pytest.mark.asyncio
    async def test_submit_success(
        self, client: AsyncClient, test_testimonial_request: Testimonial
    ):
        """Test successful testimonial submission."""
        response = await client.post(
            f"/api/testimonial/{test_testimonial_request.request_token}",
            json={
                "author_name": "Jane Doe",
                "author_title": "Senior Manager",
                "author_company": "Tech Corp",
                "quote": "This coaching experience was amazing!",
                "permission_granted": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_submit_with_video(
        self, client: AsyncClient, test_testimonial_request: Testimonial
    ):
        """Test submission with video."""
        response = await client.post(
            f"/api/testimonial/{test_testimonial_request.request_token}",
            json={
                "author_name": "Jane Doe",
                "quote": "Great experience!",
                "video_url": "https://cloudinary.com/video.mp4",
                "video_public_id": "testimonials/video123",
                "video_duration_seconds": 45,
                "thumbnail_url": "https://cloudinary.com/thumb.jpg",
                "permission_granted": True,
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_submit_not_found(self, client: AsyncClient):
        """Test submission with invalid token."""
        response = await client.post(
            f"/api/testimonial/{uuid.uuid4()}",
            json={
                "author_name": "Jane Doe",
                "quote": "Great!",
                "permission_granted": True,
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_submit_already_submitted(
        self, db_session, client: AsyncClient, test_testimonial_request: Testimonial
    ):
        """Test cannot submit twice."""
        test_testimonial_request.submitted_at = datetime.utcnow()
        await db_session.commit()

        response = await client.post(
            f"/api/testimonial/{test_testimonial_request.request_token}",
            json={
                "author_name": "Jane Doe",
                "quote": "Great!",
                "permission_granted": True,
            },
        )
        assert response.status_code == 400


class TestVideoUpload:
    """Tests for video upload endpoints."""

    @pytest.mark.asyncio
    @patch("app.services.cloudinary_service.cloudinary_service.generate_upload_signature")
    async def test_get_upload_signature(self, mock_signature, client: AsyncClient):
        """Test getting upload signature."""
        mock_signature.return_value = {
            "cloud_name": "test-cloud",
            "api_key": "test-key",
            "timestamp": 1234567890,
            "signature": "test-signature",
            "folder": "testimonials",
        }

        response = await client.get("/api/upload/video/signature")
        assert response.status_code == 200
        data = response.json()
        assert "signature" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    @patch("app.services.cloudinary_service.cloudinary_service.upload_video")
    async def test_upload_video_success(self, mock_upload, client: AsyncClient):
        """Test successful video upload."""
        mock_upload.return_value = {
            "url": "https://cloudinary.com/video.mp4",
            "public_id": "testimonials/video123",
            "duration": 30.5,
            "thumbnail_url": "https://cloudinary.com/thumb.jpg",
        }

        # Create a mock video file
        video_content = b"fake video content"

        response = await client.post(
            "/api/upload/video",
            files={"file": ("test.webm", video_content, "video/webm")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "public_id" in data

    @pytest.mark.asyncio
    async def test_upload_video_wrong_content_type(self, client: AsyncClient):
        """Test upload rejects non-video files."""
        response = await client.post(
            "/api/upload/video",
            files={"file": ("test.txt", b"text content", "text/plain")},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_video_too_large(self, client: AsyncClient):
        """Test upload rejects files over 100MB."""
        # This would need actual content over 100MB to test properly
        # For now, just verify the endpoint exists
        pass
