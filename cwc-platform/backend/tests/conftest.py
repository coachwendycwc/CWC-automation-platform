"""
Pytest fixtures for CWC Platform backend tests.
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Set test environment before importing app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.contact import Contact
from app.models.organization import Organization
from app.models.invoice import Invoice
from app.models.contract import Contract
from app.models.project import Project
from app.models.booking import Booking
from app.models.booking_type import BookingType
from app.models.client_note import ClientNote
from app.models.client_action_item import ClientActionItem
from app.models.client_goal import ClientGoal
from app.models.goal_milestone import GoalMilestone
from app.models.client_content import ClientContent
from app.models.client_session import ClientSession
from app.models.payment import Payment
from app.models.payment_plan import PaymentPlan
from app.models.recurring_invoice import RecurringInvoice
from app.models.availability import Availability, AvailabilityOverride
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.models.interaction import Interaction
from app.models.contract_template import ContractTemplate
from app.models.project_template import ProjectTemplate
from app.models.testimonial import Testimonial
from app.models.offboarding import OffboardingWorkflow, OffboardingTemplate, OffboardingActivity
from app.models.expense import Expense, ExpenseCategory, RecurringExpense
from app.models.mileage import MileageLog
from app.models.contractor import Contractor, ContractorPayment
from app.services.auth_service import create_access_token, hash_password


# Test database engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database dependency override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        name="Test User",
        password_hash=hash_password("testpass123"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_token(test_user: User) -> str:
    """Create an auth token for the test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
async def auth_headers(test_user_token: str) -> dict:
    """Return auth headers for authenticated requests."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """Create a test organization."""
    org = Organization(
        id=str(uuid.uuid4()),
        name="Test Organization",
        industry="Technology",
        website="https://test.com",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_contact(db_session: AsyncSession, test_organization: Organization) -> Contact:
    """Create a test contact."""
    contact = Contact(
        id=str(uuid.uuid4()),
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="555-1234",
        organization_id=test_organization.id,
        contact_type="client",
    )
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)
    return contact


@pytest.fixture
async def test_booking_type(db_session: AsyncSession) -> BookingType:
    """Create a test booking type."""
    booking_type = BookingType(
        id=str(uuid.uuid4()),
        name="Discovery Call",
        slug="discovery-call",
        description="30-minute discovery call",
        duration_minutes=30,
        price=0.0,
        is_active=True,
    )
    db_session.add(booking_type)
    await db_session.commit()
    await db_session.refresh(booking_type)
    return booking_type


@pytest.fixture
async def test_invoice(db_session: AsyncSession, test_contact: Contact) -> Invoice:
    """Create a test invoice."""
    invoice = Invoice(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        invoice_number="INV-001",
        status="draft",
        line_items=[
            {"description": "Coaching Session", "quantity": 1, "rate": 200.0, "amount": 200.0}
        ],
        subtotal=200.0,
        tax_rate=0.0,
        tax_amount=0.0,
        discount_amount=0.0,
        total=200.0,
        due_date=datetime.utcnow() + timedelta(days=30),
    )
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)
    return invoice


@pytest.fixture
async def test_contract(db_session: AsyncSession, test_contact: Contact) -> Contract:
    """Create a test contract."""
    contract = Contract(
        id=str(uuid.uuid4()),
        contract_number="CON-001",
        contact_id=test_contact.id,
        title="Coaching Agreement",
        content="This is a test contract content.",
        status="draft",
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)
    return contract


@pytest.fixture
async def test_project(db_session: AsyncSession, test_contact: Contact) -> Project:
    """Create a test project."""
    project = Project(
        id=str(uuid.uuid4()),
        project_number="PRJ-001",
        contact_id=test_contact.id,
        title="Test Project",
        description="A test project",
        status="active",
        start_date=datetime.utcnow().date(),
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


# Authenticated client fixture
@pytest.fixture
async def auth_client(
    client: AsyncClient,
    auth_headers: dict,
) -> AsyncClient:
    """Return a client with auth headers pre-set."""
    client.headers.update(auth_headers)
    return client


# Phase 2: Client Portal Fixtures

@pytest.fixture
async def test_client_note(db_session: AsyncSession, test_contact: Contact) -> ClientNote:
    """Create a test client note."""
    note = ClientNote(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        content="Test note content from coach",
        direction="to_client",
        is_read=False,
    )
    db_session.add(note)
    await db_session.commit()
    await db_session.refresh(note)
    return note


@pytest.fixture
async def test_action_item(db_session: AsyncSession, test_contact: Contact) -> ClientActionItem:
    """Create a test action item."""
    action_item = ClientActionItem(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        title="Complete intake form",
        description="Please fill out the intake questionnaire",
        priority="high",
        status="pending",
        due_date=datetime.utcnow().date() + timedelta(days=7),
    )
    db_session.add(action_item)
    await db_session.commit()
    await db_session.refresh(action_item)
    return action_item


@pytest.fixture
async def test_goal(db_session: AsyncSession, test_contact: Contact) -> ClientGoal:
    """Create a test goal."""
    goal = ClientGoal(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        title="Improve leadership skills",
        description="Develop better leadership and communication skills",
        category="career",
        status="active",
        target_date=datetime.utcnow().date() + timedelta(days=90),
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal, attribute_names=["milestones"])
    return goal


@pytest.fixture
async def test_milestone(db_session: AsyncSession, test_goal: ClientGoal) -> GoalMilestone:
    """Create a test milestone."""
    milestone = GoalMilestone(
        id=str(uuid.uuid4()),
        goal_id=test_goal.id,
        title="Complete leadership assessment",
        description="Take the initial assessment to identify areas for improvement",
        sort_order=1,
        is_completed=False,
    )
    db_session.add(milestone)
    await db_session.commit()
    await db_session.refresh(milestone)
    return milestone


@pytest.fixture
async def test_content(db_session: AsyncSession, test_contact: Contact) -> ClientContent:
    """Create a test content item."""
    content = ClientContent(
        id=str(uuid.uuid4()),
        title="Getting Started Guide",
        description="A guide to help you get started with coaching",
        content_type="link",
        external_url="https://example.com/guide",
        contact_id=test_contact.id,
        category="onboarding",
        is_active=True,
    )
    db_session.add(content)
    await db_session.commit()
    await db_session.refresh(content)
    return content


@pytest.fixture
async def test_client_session(db_session: AsyncSession, test_contact: Contact) -> ClientSession:
    """Create a test client session with magic link token."""
    import secrets
    session = ClientSession(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.utcnow() + timedelta(hours=24),
        is_active=True,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


# Phase 3: Payment & Billing Fixtures

@pytest.fixture
async def test_invoice_for_payment(db_session: AsyncSession, test_contact: Contact) -> Invoice:
    """Create a test invoice suitable for payments (sent status, balance due)."""
    from decimal import Decimal
    invoice = Invoice(
        id=str(uuid.uuid4()),
        invoice_number="INV-PAY-001",
        contact_id=test_contact.id,
        status="sent",
        line_items=[{"description": "Coaching Session", "quantity": 1, "unit_price": 500.00}],
        subtotal=Decimal("500.00"),
        tax_rate=None,
        tax_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total=Decimal("500.00"),
        amount_paid=Decimal("0.00"),
        due_date=datetime.utcnow().date() + timedelta(days=30),
    )
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)
    return invoice


@pytest.fixture
async def test_payment(db_session: AsyncSession, test_invoice_for_payment: Invoice) -> Payment:
    """Create a test payment for an invoice."""
    from decimal import Decimal
    payment = Payment(
        id=str(uuid.uuid4()),
        invoice_id=test_invoice_for_payment.id,
        amount=Decimal("100.00"),
        payment_method="card",
        payment_date=datetime.utcnow().date(),
        reference="TEST-REF-001",
        notes="Test payment",
    )
    db_session.add(payment)
    # Update invoice amount_paid
    test_invoice_for_payment.amount_paid = Decimal("100.00")
    await db_session.commit()
    await db_session.refresh(payment)
    return payment


@pytest.fixture
async def test_payment_plan(db_session: AsyncSession, test_invoice_for_payment: Invoice) -> PaymentPlan:
    """Create a test payment plan for an invoice."""
    from decimal import Decimal
    plan = PaymentPlan(
        id=str(uuid.uuid4()),
        invoice_id=test_invoice_for_payment.id,
        total_amount=test_invoice_for_payment.total,
        number_of_payments=3,
        payment_frequency="monthly",
        start_date=datetime.utcnow().date(),
        status="active",
    )
    plan.generate_schedule()
    # Mark invoice as having payment plan
    test_invoice_for_payment.is_payment_plan = True
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


@pytest.fixture
async def test_recurring_invoice(db_session: AsyncSession, test_contact: Contact) -> RecurringInvoice:
    """Create a test recurring invoice template."""
    from decimal import Decimal
    recurring = RecurringInvoice(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        title="Monthly Coaching Package",
        line_items=[{"description": "Monthly Coaching", "quantity": 1, "unit_price": 500.00}],
        subtotal=Decimal("500.00"),
        tax_rate=None,
        tax_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total=Decimal("500.00"),
        payment_terms="net_30",
        frequency="monthly",
        start_date=datetime.utcnow().date(),
        next_invoice_date=datetime.utcnow().date(),
        is_active=True,
        auto_send=False,
    )
    db_session.add(recurring)
    await db_session.commit()
    await db_session.refresh(recurring)
    return recurring


# Phase 4: Advanced Features Fixtures

@pytest.fixture
async def test_availability(db_session: AsyncSession, test_user: User) -> Availability:
    """Create a test availability slot."""
    availability = Availability(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        day_of_week=0,  # Monday
        start_time="09:00",
        end_time="17:00",
        is_active=True,
    )
    db_session.add(availability)
    await db_session.commit()
    await db_session.refresh(availability)
    return availability


@pytest.fixture
async def test_availability_override(db_session: AsyncSession, test_user: User) -> AvailabilityOverride:
    """Create a test availability override (blocked date)."""
    override = AvailabilityOverride(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        date=datetime.utcnow().date() + timedelta(days=7),
        is_available=False,
        reason="Vacation day",
    )
    db_session.add(override)
    await db_session.commit()
    await db_session.refresh(override)
    return override


@pytest.fixture
async def test_task(db_session: AsyncSession, test_project: Project) -> Task:
    """Create a test task."""
    task = Task(
        id=str(uuid.uuid4()),
        task_number="TSK-001",
        project_id=test_project.id,
        title="Complete project setup",
        description="Set up the project structure and initial configuration",
        status="todo",
        priority="high",
        due_date=datetime.utcnow().date() + timedelta(days=7),
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest.fixture
async def test_time_entry(db_session: AsyncSession, test_task: Task) -> TimeEntry:
    """Create a test time entry."""
    from decimal import Decimal
    entry = TimeEntry(
        id=str(uuid.uuid4()),
        task_id=test_task.id,
        description="Initial research and planning",
        hours=Decimal("2.5"),
        entry_date=datetime.utcnow().date(),
        created_by="test@example.com",
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)
    return entry


@pytest.fixture
async def test_interaction(db_session: AsyncSession, test_contact: Contact, test_user: User) -> Interaction:
    """Create a test interaction."""
    interaction = Interaction(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        interaction_type="note",
        subject="Initial consultation notes",
        content="Discussed coaching goals and expectations.",
        direction="outbound",
        created_by=test_user.id,
    )
    db_session.add(interaction)
    await db_session.commit()
    await db_session.refresh(interaction)
    return interaction


@pytest.fixture
async def test_contract_template(db_session: AsyncSession) -> ContractTemplate:
    """Create a test contract template."""
    template = ContractTemplate(
        id=str(uuid.uuid4()),
        name="Coaching Agreement Template",
        description="Standard coaching agreement for new clients",
        content="This agreement is between {{client_name}} and the Coach. Services: {{services}}. Total: {{total_amount}}.",
        category="coaching",
        merge_fields=["client_name", "services", "total_amount"],
        default_expiry_days=7,
        is_active=True,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest.fixture
async def test_project_template(db_session: AsyncSession) -> ProjectTemplate:
    """Create a test project template."""
    from decimal import Decimal
    template = ProjectTemplate(
        id=str(uuid.uuid4()),
        name="Standard Coaching Program",
        description="12-week coaching program template",
        project_type="coaching",
        default_duration_days=84,
        estimated_hours=Decimal("24.0"),
        task_templates=[
            {"title": "Initial Assessment", "description": "Complete intake and assessment", "estimated_hours": 2.0, "order_index": 0},
            {"title": "Goal Setting Session", "description": "Define coaching goals", "estimated_hours": 1.5, "order_index": 1},
            {"title": "Weekly Check-ins", "description": "Regular progress reviews", "estimated_hours": 12.0, "order_index": 2},
        ],
        is_active=True,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


# Phase 5: Testimonials & Feedback Fixtures

@pytest.fixture
async def test_testimonial(db_session: AsyncSession, test_contact: Contact) -> Testimonial:
    """Create a test testimonial."""
    import secrets
    testimonial = Testimonial(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        author_name="Jane Doe",
        author_title="CEO",
        author_company="Test Company",
        quote="Working with this coach transformed my leadership approach.",
        status="pending",
        permission_granted=False,
        featured=False,
        request_token=secrets.token_urlsafe(32),
    )
    db_session.add(testimonial)
    await db_session.commit()
    await db_session.refresh(testimonial)
    return testimonial


@pytest.fixture
async def test_offboarding_template(db_session: AsyncSession) -> OffboardingTemplate:
    """Create a test offboarding template."""
    template = OffboardingTemplate(
        id=str(uuid.uuid4()),
        name="Client Offboarding Template",
        description="Standard offboarding process for coaching clients",
        workflow_type="client",
        checklist_items=[
            "Send final invoice",
            "Schedule closing session",
            "Send survey link",
            "Request testimonial",
            "Archive project files",
        ],
        survey_delay_days=3,
        testimonial_delay_days=7,
        is_active=True,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest.fixture
async def test_offboarding_workflow(
    db_session: AsyncSession, test_contact: Contact, test_project: Project
) -> OffboardingWorkflow:
    """Create a test offboarding workflow."""
    import secrets
    workflow = OffboardingWorkflow(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        workflow_type="project",
        related_project_id=test_project.id,
        status="pending",
        checklist=[
            {"item": "Send final invoice", "completed": False},
            {"item": "Schedule closing session", "completed": True, "completed_at": datetime.utcnow().isoformat()},
            {"item": "Send survey link", "completed": False},
        ],
        send_survey=True,
        request_testimonial=True,
        survey_token=secrets.token_urlsafe(32),
        testimonial_token=secrets.token_urlsafe(32),
    )
    db_session.add(workflow)
    await db_session.commit()
    await db_session.refresh(workflow)
    return workflow


# Phase 6: Integrations & Utilities Fixtures

@pytest.fixture
async def test_expense_category(db_session: AsyncSession) -> ExpenseCategory:
    """Create a test expense category."""
    category = ExpenseCategory(
        id=str(uuid.uuid4()),
        name="Software & Subscriptions",
        description="Software tools and SaaS subscriptions",
        color="#8b5cf6",
        icon="laptop",
        is_tax_deductible=True,
        is_active=True,
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest.fixture
async def test_expense(db_session: AsyncSession, test_expense_category: ExpenseCategory) -> Expense:
    """Create a test expense."""
    from decimal import Decimal
    expense = Expense(
        id=str(uuid.uuid4()),
        description="Zoom subscription",
        amount=Decimal("14.99"),
        expense_date=datetime.utcnow().date(),
        category_id=test_expense_category.id,
        vendor="Zoom",
        payment_method="card",
        is_tax_deductible=True,
        tax_year=datetime.utcnow().year,
    )
    db_session.add(expense)
    await db_session.commit()
    await db_session.refresh(expense)
    return expense


@pytest.fixture
async def test_recurring_expense(db_session: AsyncSession, test_expense_category: ExpenseCategory) -> RecurringExpense:
    """Create a test recurring expense."""
    from decimal import Decimal
    recurring = RecurringExpense(
        id=str(uuid.uuid4()),
        description="Monthly software subscription",
        amount=Decimal("29.99"),
        vendor="Adobe",
        category_id=test_expense_category.id,
        frequency="monthly",
        start_date=datetime.utcnow().date(),
        next_due_date=datetime.utcnow().date() + timedelta(days=30),
        is_active=True,
    )
    db_session.add(recurring)
    await db_session.commit()
    await db_session.refresh(recurring)
    return recurring


@pytest.fixture
async def test_mileage_log(db_session: AsyncSession) -> MileageLog:
    """Create a test mileage log."""
    from decimal import Decimal
    log = MileageLog(
        id=str(uuid.uuid4()),
        trip_date=datetime.utcnow().date(),
        description="Client meeting downtown",
        purpose="client_meeting",
        miles=Decimal("25.5"),
        rate_per_mile=Decimal("0.67"),
        total_deduction=Decimal("17.09"),
        start_location="Home Office",
        end_location="Client Office",
        round_trip=False,
        tax_year=datetime.utcnow().year,
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)
    return log


@pytest.fixture
async def test_contractor(db_session: AsyncSession) -> Contractor:
    """Create a test contractor."""
    contractor = Contractor(
        id=str(uuid.uuid4()),
        name="Jane Smith",
        business_name="Smith Consulting LLC",
        email="jane@smithconsulting.com",
        phone="555-9876",
        tax_id_type="ein",
        w9_on_file=True,
        w9_received_date=datetime.utcnow().date(),
        service_type="Virtual Assistant",
        is_active=True,
    )
    db_session.add(contractor)
    await db_session.commit()
    await db_session.refresh(contractor)
    return contractor


@pytest.fixture
async def test_contractor_payment(db_session: AsyncSession, test_contractor: Contractor) -> ContractorPayment:
    """Create a test contractor payment."""
    from decimal import Decimal
    payment = ContractorPayment(
        id=str(uuid.uuid4()),
        contractor_id=test_contractor.id,
        amount=Decimal("500.00"),
        payment_date=datetime.utcnow().date(),
        description="Virtual assistant services - January",
        payment_method="bank_transfer",
        tax_year=datetime.utcnow().year,
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)
    return payment
