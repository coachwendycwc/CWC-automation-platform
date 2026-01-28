"""
Tests for Onboarding Assessment endpoints.
"""
import pytest
from datetime import datetime
import uuid
import secrets

from httpx import AsyncClient
from sqlalchemy import select

from app.models.contact import Contact
from app.models.onboarding_assessment import OnboardingAssessment


@pytest.fixture
async def test_assessment(db_session, test_contact: Contact) -> OnboardingAssessment:
    """Create a test onboarding assessment."""
    assessment = OnboardingAssessment(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        token=secrets.token_urlsafe(32),
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)
    return assessment


@pytest.fixture
async def test_completed_assessment(db_session, test_contact: Contact) -> OnboardingAssessment:
    """Create a completed onboarding assessment."""
    assessment = OnboardingAssessment(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        token=secrets.token_urlsafe(32),
        completed_at=datetime.utcnow(),
        primary_coaching_goal="Career advancement",
        biggest_challenge="Work-life balance",
        success_definition="Getting promoted within 6 months",
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)
    return assessment


class TestPublicGetAssessment:
    """Tests for public assessment retrieval by token."""

    @pytest.mark.asyncio
    async def test_get_assessment_by_token(
        self, client: AsyncClient, test_assessment: OnboardingAssessment
    ):
        """Test getting assessment info by token."""
        response = await client.get(f"/api/onboarding/{test_assessment.token}")
        assert response.status_code == 200
        data = response.json()
        assert "contact_name" in data
        assert data["already_completed"] is False

    @pytest.mark.asyncio
    async def test_get_assessment_not_found(self, client: AsyncClient):
        """Test getting assessment with invalid token."""
        response = await client.get(f"/api/onboarding/{secrets.token_urlsafe(32)}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_completed_assessment_shows_status(
        self, client: AsyncClient, test_completed_assessment: OnboardingAssessment
    ):
        """Test completed assessment shows already_completed status."""
        response = await client.get(f"/api/onboarding/{test_completed_assessment.token}")
        assert response.status_code == 200
        data = response.json()
        assert data["already_completed"] is True


class TestPublicSubmitAssessment:
    """Tests for public assessment submission."""

    @pytest.mark.asyncio
    async def test_submit_assessment_success(
        self, client: AsyncClient, test_assessment: OnboardingAssessment
    ):
        """Test successful assessment submission."""
        response = await client.post(
            f"/api/onboarding/{test_assessment.token}",
            json={
                "primary_coaching_goal": "Improve leadership skills",
                "biggest_challenge": "Managing remote teams",
                "success_definition": "Building a high-performing team",
                "preferred_communication_style": "Direct and clear",
                "availability_preferences": "Mornings",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_submit_assessment_not_found(self, client: AsyncClient):
        """Test submission with invalid token."""
        response = await client.post(
            f"/api/onboarding/{secrets.token_urlsafe(32)}",
            json={
                "primary_coaching_goal": "Test goal",
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_submit_already_completed(
        self, client: AsyncClient, test_completed_assessment: OnboardingAssessment
    ):
        """Test cannot submit already completed assessment."""
        response = await client.post(
            f"/api/onboarding/{test_completed_assessment.token}",
            json={
                "primary_coaching_goal": "New goal",
            },
        )
        assert response.status_code == 400


class TestAdminListAssessments:
    """Tests for admin assessment listing."""

    @pytest.mark.asyncio
    async def test_list_assessments_unauthenticated(self, client: AsyncClient):
        """Test listing assessments requires authentication."""
        response = await client.get("/api/onboarding-assessments")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_assessments_success(
        self, auth_client: AsyncClient, test_assessment: OnboardingAssessment
    ):
        """Test listing assessments as admin."""
        response = await auth_client.get("/api/onboarding-assessments")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_list_assessments_filter_completed(
        self, auth_client: AsyncClient, test_completed_assessment: OnboardingAssessment
    ):
        """Test filtering completed assessments."""
        response = await auth_client.get(
            "/api/onboarding-assessments",
            params={"status": "completed"},
        )
        assert response.status_code == 200
        data = response.json()
        for assessment in data:
            assert assessment["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_list_assessments_filter_pending(
        self, auth_client: AsyncClient, test_assessment: OnboardingAssessment
    ):
        """Test filtering pending assessments."""
        response = await auth_client.get(
            "/api/onboarding-assessments",
            params={"status": "pending"},
        )
        assert response.status_code == 200
        data = response.json()
        for assessment in data:
            assert assessment["completed_at"] is None


class TestAdminGetAssessment:
    """Tests for admin getting assessment details."""

    @pytest.mark.asyncio
    async def test_get_assessment_unauthenticated(
        self, client: AsyncClient, test_assessment: OnboardingAssessment
    ):
        """Test getting assessment requires authentication."""
        response = await client.get(f"/api/onboarding-assessments/{test_assessment.id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_assessment_success(
        self, auth_client: AsyncClient, test_completed_assessment: OnboardingAssessment
    ):
        """Test getting assessment details."""
        response = await auth_client.get(
            f"/api/onboarding-assessments/{test_completed_assessment.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_completed_assessment.id
        assert data["primary_coaching_goal"] == "Career advancement"

    @pytest.mark.asyncio
    async def test_get_assessment_not_found(self, auth_client: AsyncClient):
        """Test getting non-existent assessment."""
        response = await auth_client.get(f"/api/onboarding-assessments/{uuid.uuid4()}")
        assert response.status_code == 404


class TestGetAssessmentForContact:
    """Tests for getting assessment by contact ID."""

    @pytest.mark.asyncio
    async def test_get_assessment_for_contact(
        self, auth_client: AsyncClient, test_assessment: OnboardingAssessment, test_contact: Contact
    ):
        """Test getting assessment by contact ID."""
        response = await auth_client.get(f"/api/contacts/{test_contact.id}/onboarding")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_assessment.id

    @pytest.mark.asyncio
    async def test_get_assessment_for_contact_not_exists(
        self, db_session, auth_client: AsyncClient
    ):
        """Test getting assessment for contact without one."""
        # Create a contact without assessment
        from app.models.contact import Contact
        contact = Contact(
            id=str(uuid.uuid4()),
            first_name="No",
            last_name="Assessment",
            email="no-assessment@example.com",
        )
        db_session.add(contact)
        await db_session.commit()

        response = await auth_client.get(f"/api/contacts/{contact.id}/onboarding")
        assert response.status_code == 200
        assert response.json() is None


class TestCreateAssessmentForContact:
    """Tests for creating assessment for a contact."""

    @pytest.mark.asyncio
    async def test_create_assessment_success(
        self, db_session, auth_client: AsyncClient
    ):
        """Test creating assessment for contact."""
        # Create a contact without assessment
        contact = Contact(
            id=str(uuid.uuid4()),
            first_name="New",
            last_name="Contact",
            email="new-contact@example.com",
        )
        db_session.add(contact)
        await db_session.commit()

        response = await auth_client.post(f"/api/contacts/{contact.id}/onboarding/create")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "token" in data
        assert "assessment_url" in data

    @pytest.mark.asyncio
    async def test_create_assessment_contact_not_found(self, auth_client: AsyncClient):
        """Test creating assessment for non-existent contact."""
        response = await auth_client.post(f"/api/contacts/{uuid.uuid4()}/onboarding/create")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_assessment_already_exists(
        self, auth_client: AsyncClient, test_assessment: OnboardingAssessment, test_contact: Contact
    ):
        """Test cannot create duplicate assessment."""
        response = await auth_client.post(f"/api/contacts/{test_contact.id}/onboarding/create")
        assert response.status_code == 400


class TestResendAssessmentEmail:
    """Tests for resending assessment email."""

    @pytest.mark.asyncio
    async def test_resend_email_success(
        self, auth_client: AsyncClient, test_assessment: OnboardingAssessment, test_contact: Contact
    ):
        """Test resending assessment email."""
        response = await auth_client.post(f"/api/contacts/{test_contact.id}/onboarding/resend")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_resend_email_not_found(self, auth_client: AsyncClient):
        """Test resending for non-existent assessment."""
        response = await auth_client.post(f"/api/contacts/{uuid.uuid4()}/onboarding/resend")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_resend_email_already_completed(
        self, auth_client: AsyncClient, test_completed_assessment: OnboardingAssessment, test_contact: Contact
    ):
        """Test cannot resend for completed assessment."""
        # Need to make sure test_completed_assessment uses test_contact
        response = await auth_client.post(f"/api/contacts/{test_completed_assessment.contact_id}/onboarding/resend")
        assert response.status_code == 400
