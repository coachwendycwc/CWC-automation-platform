from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.services.reminder_service import reminder_service
from app.services.offboarding_scheduler import offboarding_scheduler
from app.services.recurring_invoice_scheduler import recurring_invoice_scheduler
from app.services.workflow_scheduler import workflow_scheduler
from app.routers import (
    auth_router,
    users_router,
    organizations_router,
    contacts_router,
    interactions_router,
    webhooks_router,
    booking_types_router,
    availability_router,
    bookings_router,
    public_booking_router,
    invoices_router,
    payments_router,
    payment_plans_router,
    public_invoice_router,
    contract_templates_router,
    contracts_router,
    public_contract_router,
    project_templates_router,
    projects_router,
    tasks_router,
    integrations_router,
    stripe_router,
    extractions_router,
    reports_router,
    reminders_router,
    expenses_router,
    mileage_router,
    contractors_router,
    offboarding_router,
    offboarding_templates_router,
    feedback_router,
    client_auth_router,
    client_portal_router,
    content_router,
    notes_router,
    action_items_router,
    goals_router,
    testimonials_router,
    testimonial_public_router,
    subscriptions_router,
    recurring_invoices_router,
    assessments_router,
    onboarding_assessment_router,
    icf_tracker_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - start/stop background services."""
    # Startup
    await reminder_service.start()
    await offboarding_scheduler.start()
    await recurring_invoice_scheduler.start()
    await workflow_scheduler.start()
    yield
    # Shutdown
    await workflow_scheduler.stop()
    await recurring_invoice_scheduler.stop()
    await offboarding_scheduler.stop()
    await reminder_service.stop()


app = FastAPI(
    title="CWC Platform API",
    description="Unified business platform for Coaching Women of Color",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:3001", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(organizations_router, prefix="/api")
app.include_router(contacts_router, prefix="/api")
app.include_router(interactions_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
app.include_router(booking_types_router, prefix="/api")
app.include_router(availability_router, prefix="/api")
app.include_router(bookings_router, prefix="/api")
app.include_router(public_booking_router, prefix="/api")
app.include_router(invoices_router)  # Already has /api prefix
app.include_router(payments_router)  # Already has /api prefix
app.include_router(payment_plans_router)  # Already has /api prefix
app.include_router(public_invoice_router)  # Already has /api prefix
app.include_router(contract_templates_router)  # Already has /api prefix
app.include_router(contracts_router)  # Already has /api prefix
app.include_router(public_contract_router)  # Already has /api prefix
app.include_router(project_templates_router)  # Already has /api prefix
app.include_router(projects_router)  # Already has /api prefix
app.include_router(tasks_router)  # Already has /api prefix
app.include_router(integrations_router)  # Already has /api prefix
app.include_router(stripe_router)  # Already has /api prefix
app.include_router(extractions_router)  # Already has /api prefix
app.include_router(reports_router)  # Already has /api prefix
app.include_router(reminders_router)  # Already has /api prefix
app.include_router(expenses_router)  # Already has /api prefix
app.include_router(mileage_router)  # Already has /api prefix
app.include_router(contractors_router)  # Already has /api prefix
app.include_router(offboarding_router)  # Already has /api prefix
app.include_router(offboarding_templates_router)  # Already has /api prefix
app.include_router(feedback_router)  # Already has /api prefix
app.include_router(client_auth_router)  # Already has /api prefix
app.include_router(client_portal_router)  # Already has /api prefix
app.include_router(content_router, prefix="/api")  # Admin content management
app.include_router(notes_router, prefix="/api")  # Client notes
app.include_router(action_items_router, prefix="/api")  # Client action items
app.include_router(goals_router)  # Already has /api prefix
app.include_router(testimonial_public_router)  # Already has /api prefix - MUST be before testimonials_router
app.include_router(testimonials_router)  # Already has /api prefix
app.include_router(subscriptions_router)  # Already has /api prefix
app.include_router(recurring_invoices_router)  # Already has /api prefix
app.include_router(assessments_router)  # Already has /api prefix
app.include_router(onboarding_assessment_router)  # Already has /api prefix
app.include_router(icf_tracker_router)  # Already has /api prefix


@app.get("/")
async def root():
    return {
        "name": "CWC Platform API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
