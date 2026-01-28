from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.organizations import router as organizations_router
from app.routers.contacts import router as contacts_router
from app.routers.interactions import router as interactions_router
from app.routers.webhooks import router as webhooks_router
from app.routers.booking_types import router as booking_types_router
from app.routers.availability import router as availability_router
from app.routers.bookings import router as bookings_router
from app.routers.public_booking import router as public_booking_router
from app.routers.invoices import router as invoices_router
from app.routers.payments import router as payments_router
from app.routers.payment_plans import router as payment_plans_router
from app.routers.public_invoice import router as public_invoice_router
from app.routers.contract_templates import router as contract_templates_router
from app.routers.contracts import router as contracts_router
from app.routers.public_contract import router as public_contract_router
from app.routers.project_templates import router as project_templates_router
from app.routers.projects import router as projects_router
from app.routers.tasks import router as tasks_router
from app.routers.integrations import router as integrations_router
from app.routers.stripe import router as stripe_router
from app.routers.extractions import router as extractions_router
from app.routers.reports import router as reports_router
from app.routers.reminders import router as reminders_router
from app.routers.expenses import router as expenses_router
from app.routers.mileage import router as mileage_router
from app.routers.contractors import router as contractors_router
from app.routers.offboarding import router as offboarding_router
from app.routers.offboarding import templates_router as offboarding_templates_router
from app.routers.feedback import router as feedback_router
from app.routers.client_auth import router as client_auth_router
from app.routers.client_portal import router as client_portal_router
from app.routers.content import router as content_router
from app.routers.notes import router as notes_router
from app.routers.action_items import router as action_items_router
from app.routers.goals import router as goals_router
from app.routers.testimonials import router as testimonials_router
from app.routers.testimonial_public import router as testimonial_public_router
from app.routers.subscriptions import router as subscriptions_router
from app.routers.recurring_invoices import router as recurring_invoices_router
from app.routers.organizational_assessments import router as assessments_router
from app.routers.onboarding_assessment import router as onboarding_assessment_router
from app.routers.icf_tracker import router as icf_tracker_router

__all__ = [
    "auth_router",
    "users_router",
    "organizations_router",
    "contacts_router",
    "interactions_router",
    "webhooks_router",
    "booking_types_router",
    "availability_router",
    "bookings_router",
    "public_booking_router",
    "invoices_router",
    "payments_router",
    "payment_plans_router",
    "public_invoice_router",
    "contract_templates_router",
    "contracts_router",
    "public_contract_router",
    "project_templates_router",
    "projects_router",
    "tasks_router",
    "integrations_router",
    "stripe_router",
    "extractions_router",
    "reports_router",
    "reminders_router",
    "expenses_router",
    "mileage_router",
    "contractors_router",
    "offboarding_router",
    "offboarding_templates_router",
    "feedback_router",
    "client_auth_router",
    "client_portal_router",
    "content_router",
    "notes_router",
    "action_items_router",
    "goals_router",
    "testimonials_router",
    "testimonial_public_router",
    "subscriptions_router",
    "recurring_invoices_router",
    "assessments_router",
    "onboarding_assessment_router",
    "icf_tracker_router",
]
