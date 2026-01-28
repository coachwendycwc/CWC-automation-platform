"""
Tests for Organizational Assessments endpoints.
"""
import pytest
from datetime import datetime
import uuid

from httpx import AsyncClient
from sqlalchemy import select

from app.models.contact import Contact
from app.models.organization import Organization
from app.models.organizational_assessment import OrganizationalAssessment


@pytest.fixture
async def test_org_assessment(db_session, test_contact: Contact, test_organization: Organization) -> OrganizationalAssessment:
    """Create a test organizational assessment."""
    assessment = OrganizationalAssessment(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        organization_id=test_organization.id,
        full_name="Jane Doe",
        title_role="HR Director",
        organization_name=test_organization.name,
        work_email="jane@testorg.com",
        phone_number="555-1234",
        areas_of_interest=["leadership_development", "team_building"],
        desired_outcomes=["improved_team_performance"],
        current_challenge="Team collaboration needs improvement",
        primary_audience=["managers", "executives"],
        participant_count="10-25",
        preferred_format="in_person",
        budget_range="5000-10000",
        ideal_timeline="q2_2024",
        status="submitted",
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)
    return assessment


class TestSubmitAssessment:
    """Tests for public assessment submission."""

    @pytest.mark.asyncio
    async def test_submit_assessment_success(self, client: AsyncClient):
        """Test successful assessment submission."""
        response = await client.post(
            "/api/assessments/organizations/submit",
            json={
                "full_name": "John Smith",
                "title_role": "CEO",
                "organization_name": "New Corp",
                "work_email": "john@newcorp.com",
                "phone_number": "555-5555",
                "organization_website": "https://newcorp.com",
                "areas_of_interest": ["executive_coaching", "dei_training"],
                "desired_outcomes": ["improved_leadership"],
                "current_challenge": "Leadership development needed",
                "primary_audience": ["executives"],
                "participant_count": "1-9",
                "preferred_format": "virtual",
                "budget_range": "under_5000",
                "ideal_timeline": "immediate",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "booking_url" in data

    @pytest.mark.asyncio
    async def test_submit_assessment_creates_contact_and_org(
        self, db_session, client: AsyncClient
    ):
        """Test submission creates contact and organization."""
        response = await client.post(
            "/api/assessments/organizations/submit",
            json={
                "full_name": "Alice Johnson",
                "title_role": "VP Operations",
                "organization_name": "Brand New Company",
                "work_email": "alice@brandnew.com",
                "areas_of_interest": ["team_building"],
                "desired_outcomes": ["improved_collaboration"],
                "current_challenge": "Team silos",
                "primary_audience": ["all_employees"],
                "participant_count": "50+",
                "preferred_format": "hybrid",
                "budget_range": "10000+",
                "ideal_timeline": "q3_2024",
            },
        )
        assert response.status_code == 201

        # Verify organization was created
        result = await db_session.execute(
            select(Organization).where(Organization.name == "Brand New Company")
        )
        org = result.scalar_one_or_none()
        assert org is not None

        # Verify contact was created
        result = await db_session.execute(
            select(Contact).where(Contact.email == "alice@brandnew.com")
        )
        contact = result.scalar_one_or_none()
        assert contact is not None
        assert contact.first_name == "Alice"

    @pytest.mark.asyncio
    async def test_submit_assessment_existing_contact(
        self, client: AsyncClient, test_contact: Contact
    ):
        """Test submission with existing contact email."""
        response = await client.post(
            "/api/assessments/organizations/submit",
            json={
                "full_name": f"{test_contact.first_name} {test_contact.last_name or ''}".strip(),
                "title_role": "Manager",
                "organization_name": "Existing Contact Org",
                "work_email": test_contact.email,
                "areas_of_interest": ["coaching"],
                "desired_outcomes": ["growth"],
                "current_challenge": "Challenge",
                "primary_audience": ["individuals"],
                "participant_count": "1-9",
                "preferred_format": "virtual",
                "budget_range": "under_5000",
                "ideal_timeline": "flexible",
            },
        )
        assert response.status_code == 201


class TestListAssessments:
    """Tests for listing assessments."""

    @pytest.mark.asyncio
    async def test_list_assessments_empty(self, auth_client: AsyncClient):
        """Test listing assessments when none exist."""
        response = await auth_client.get("/api/assessments")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_assessments_with_data(
        self, auth_client: AsyncClient, test_org_assessment: OrganizationalAssessment
    ):
        """Test listing assessments with data."""
        response = await auth_client.get("/api/assessments")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_assessments_filter_by_status(
        self, auth_client: AsyncClient, test_org_assessment: OrganizationalAssessment
    ):
        """Test filtering assessments by status."""
        response = await auth_client.get(
            "/api/assessments",
            params={"status": "submitted"},
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_list_assessments_search(
        self, auth_client: AsyncClient, test_org_assessment: OrganizationalAssessment
    ):
        """Test searching assessments."""
        response = await auth_client.get(
            "/api/assessments",
            params={"search": "Jane"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_assessments_pagination(
        self, auth_client: AsyncClient, test_org_assessment: OrganizationalAssessment
    ):
        """Test assessment pagination."""
        response = await auth_client.get(
            "/api/assessments",
            params={"skip": 0, "limit": 10},
        )
        assert response.status_code == 200


class TestGetAssessmentStats:
    """Tests for assessment statistics."""

    @pytest.mark.asyncio
    async def test_get_stats(self, auth_client: AsyncClient):
        """Test getting assessment stats."""
        response = await auth_client.get("/api/assessments/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "submitted" in data

    @pytest.mark.asyncio
    async def test_get_stats_with_data(
        self, auth_client: AsyncClient, test_org_assessment: OrganizationalAssessment
    ):
        """Test stats reflect existing data."""
        response = await auth_client.get("/api/assessments/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["submitted"] >= 1


class TestGetAssessment:
    """Tests for getting single assessment."""

    @pytest.mark.asyncio
    async def test_get_assessment_success(
        self, auth_client: AsyncClient, test_org_assessment: OrganizationalAssessment
    ):
        """Test getting assessment by ID."""
        response = await auth_client.get(f"/api/assessments/{test_org_assessment.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_org_assessment.id
        assert data["organization_name"] == test_org_assessment.organization_name

    @pytest.mark.asyncio
    async def test_get_assessment_not_found(self, auth_client: AsyncClient):
        """Test getting non-existent assessment."""
        response = await auth_client.get(f"/api/assessments/{uuid.uuid4()}")
        assert response.status_code == 404


class TestUpdateAssessment:
    """Tests for updating assessments."""

    @pytest.mark.asyncio
    async def test_update_assessment_status(
        self, auth_client: AsyncClient, test_org_assessment: OrganizationalAssessment
    ):
        """Test updating assessment status."""
        response = await auth_client.put(
            f"/api/assessments/{test_org_assessment.id}",
            json={"status": "reviewed"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewed"

    @pytest.mark.asyncio
    async def test_update_assessment_not_found(self, auth_client: AsyncClient):
        """Test updating non-existent assessment."""
        response = await auth_client.put(
            f"/api/assessments/{uuid.uuid4()}",
            json={"status": "reviewed"},
        )
        assert response.status_code == 404


class TestDeleteAssessment:
    """Tests for deleting assessments."""

    @pytest.mark.asyncio
    async def test_delete_assessment_success(
        self, db_session, auth_client: AsyncClient, test_org_assessment: OrganizationalAssessment
    ):
        """Test successful assessment deletion."""
        assessment_id = test_org_assessment.id
        response = await auth_client.delete(f"/api/assessments/{assessment_id}")
        assert response.status_code == 200

        # Verify deletion
        result = await db_session.execute(
            select(OrganizationalAssessment).where(
                OrganizationalAssessment.id == assessment_id
            )
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_assessment_not_found(self, auth_client: AsyncClient):
        """Test deleting non-existent assessment."""
        response = await auth_client.delete(f"/api/assessments/{uuid.uuid4()}")
        assert response.status_code == 404
