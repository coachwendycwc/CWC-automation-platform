"""
Client Portal Data Router.
Provides authenticated access to client data.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status, Response, Request
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.contact import Contact
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.contract import Contract
from app.models.booking import Booking
from app.models.booking_type import BookingType
from app.models.project import Project
from app.models.task import Task
from app.models.organization import Organization
from app.models.fathom_webhook import FathomWebhook
from app.models.client_content import ClientContent
from app.models.client_note import ClientNote
from app.models.client_action_item import ClientActionItem
from app.models.client_goal import ClientGoal
from app.models.goal_milestone import GoalMilestone
from app.models.onboarding_assessment import OnboardingAssessment
from app.services.client_auth_service import ClientAuthService
from app.services.pdf_service import pdf_service
from app.services.email_service import email_service
from app.config import get_settings
from app.models.portal_audit_log import PortalAuditLog
from app.schemas.client import (
    DashboardResponse,
    DashboardStats,
    ClientInvoiceSummary,
    ClientInvoiceDetail,
    ClientLineItem,
    ClientPaymentSummary,
    ClientContractSummary,
    ClientContractDetail,
    ClientBookingSummary,
    ClientBookingDetail,
    ClientProjectSummary,
    ClientProjectDetail,
    ClientTaskSummary,
    ClientProfile,
    ClientProfileUpdate,
    ClientSessionRecordingSummary,
    ClientSessionRecordingDetail,
    ClientHomeworkItem,
    OrgDashboardResponse,
    OrgBillingSummary,
    OrgUsageStats,
    OrgEmployeeSummary,
    ClientContentSummary,
    ClientContentDetail,
)
from app.schemas.note import (
    ClientNoteCreate,
    ClientNoteResponse,
)
from app.schemas.action_item import (
    ClientActionItemResponse,
    ClientActionItemStatusUpdate,
)
from app.schemas.goal import (
    ClientGoalResponse,
    ClientMilestoneComplete,
    MilestoneResponse,
)
from app.schemas.onboarding_assessment import OnboardingAssessmentResponse

router = APIRouter(prefix="/api/client", tags=["Client Portal"])


def get_client_ip(request: Request) -> str:
    """Get client IP from request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def log_portal_action(
    db: AsyncSession,
    contact_id: str,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    ip_address: str = None,
):
    """Log a portal access action."""
    log_entry = PortalAuditLog.log_action(
        contact_id=contact_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
    )
    db.add(log_entry)
    await db.commit()


async def get_current_client(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> Contact:
    """Dependency to get current authenticated client."""
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    service = ClientAuthService(db)
    return await service.get_current_client(token)


def get_contact_filter(contact: Contact):
    """
    Get filter for contact's data.
    Regular contacts only see their own data.
    Org admins also see org-wide data.
    """
    if contact.is_org_admin and contact.organization_id:
        return or_(
            Invoice.contact_id == contact.id,
            Invoice.organization_id == contact.organization_id,
        )
    return Invoice.contact_id == contact.id


# ============ Dashboard ============

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    view_mode: Literal["personal", "organization"] = Query("personal"),
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get client dashboard with stats and recent items."""

    # Build filters based on access level and view mode
    show_org = view_mode == "organization" and contact.is_org_admin and contact.organization_id

    if show_org:
        invoice_filter = or_(
            Invoice.contact_id == contact.id,
            Invoice.organization_id == contact.organization_id,
        )
        contract_filter = or_(
            Contract.contact_id == contact.id,
            Contract.organization_id == contact.organization_id,
        )
        project_filter = or_(
            Project.contact_id == contact.id,
            Project.organization_id == contact.organization_id,
        )
    else:
        invoice_filter = Invoice.contact_id == contact.id
        contract_filter = Contract.contact_id == contact.id
        project_filter = Project.contact_id == contact.id

    # Count unpaid invoices and total due
    result = await db.execute(
        select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.balance_due), 0),
        ).where(
            invoice_filter,
            Invoice.status.in_(["sent", "viewed", "partial"]),
        )
    )
    unpaid_count, total_due = result.one()

    # Count upcoming bookings
    result = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.contact_id == contact.id,
            Booking.status == "confirmed",
            Booking.start_time > datetime.utcnow(),
        )
    )
    upcoming_bookings = result.scalar()

    # Count active projects
    result = await db.execute(
        select(func.count(Project.id)).where(
            project_filter,
            Project.status.in_(["planning", "in_progress"]),
            Project.client_visible == True,
        )
    )
    active_projects = result.scalar()

    # Count pending contracts
    result = await db.execute(
        select(func.count(Contract.id)).where(
            contract_filter,
            Contract.status.in_(["sent", "viewed"]),
        )
    )
    pending_contracts = result.scalar()

    # Get recent invoices
    result = await db.execute(
        select(Invoice)
        .where(invoice_filter)
        .order_by(Invoice.created_at.desc())
        .limit(5)
    )
    recent_invoices = [
        ClientInvoiceSummary(
            id=inv.id,
            invoice_number=inv.invoice_number,
            created_at=inv.created_at,
            due_date=inv.due_date,
            total=float(inv.total),
            balance_due=float(inv.balance_due),
            status=inv.status,
        )
        for inv in result.scalars()
    ]

    # Get upcoming bookings
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.booking_type))
        .where(
            Booking.contact_id == contact.id,
            Booking.status == "confirmed",
            Booking.start_time > datetime.utcnow(),
        )
        .order_by(Booking.start_time)
        .limit(5)
    )
    upcoming_booking_list = [
        ClientBookingSummary(
            id=b.id,
            booking_type_name=b.booking_type.name if b.booking_type else "Session",
            start_time=b.start_time,
            end_time=b.end_time,
            status=b.status,
            meeting_link=b.zoom_meeting_url,
        )
        for b in result.scalars()
    ]

    return DashboardResponse(
        stats=DashboardStats(
            unpaid_invoices=unpaid_count,
            total_due=float(total_due),
            upcoming_bookings=upcoming_bookings,
            active_projects=active_projects,
            pending_contracts=pending_contracts,
        ),
        recent_invoices=recent_invoices,
        upcoming_bookings=upcoming_booking_list,
    )


# ============ Invoices ============

@router.get("/invoices", response_model=List[ClientInvoiceSummary])
async def list_invoices(
    status_filter: Optional[str] = None,
    view_mode: Literal["personal", "organization"] = Query("personal"),
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """List client's invoices."""
    show_org = view_mode == "organization" and contact.is_org_admin and contact.organization_id

    if show_org:
        base_filter = or_(
            Invoice.contact_id == contact.id,
            Invoice.organization_id == contact.organization_id,
        )
    else:
        base_filter = Invoice.contact_id == contact.id

    query = select(Invoice).options(selectinload(Invoice.contact)).where(base_filter)

    if status_filter:
        query = query.where(Invoice.status == status_filter)

    query = query.order_by(Invoice.created_at.desc())

    result = await db.execute(query)

    invoices = []
    for inv in result.scalars():
        contact_name = None
        if show_org and inv.contact and inv.contact_id != contact.id:
            contact_name = f"{inv.contact.first_name} {inv.contact.last_name or ''}".strip()
        invoices.append(
            ClientInvoiceSummary(
                id=inv.id,
                invoice_number=inv.invoice_number,
                created_at=inv.created_at,
                due_date=inv.due_date,
                total=float(inv.total),
                balance_due=float(inv.balance_due),
                status=inv.status,
                contact_name=contact_name,
            )
        )
    return invoices


@router.get("/invoices/{invoice_id}", response_model=ClientInvoiceDetail)
async def get_invoice(
    invoice_id: str,
    request: Request,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get invoice detail."""
    # Log access
    await log_portal_action(
        db, contact.id, "view_invoice", "invoice", invoice_id, get_client_ip(request)
    )
    if contact.is_org_admin and contact.organization_id:
        base_filter = or_(
            Invoice.contact_id == contact.id,
            Invoice.organization_id == contact.organization_id,
        )
    else:
        base_filter = Invoice.contact_id == contact.id

    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.payments))
        .where(Invoice.id == invoice_id, base_filter)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    line_items = invoice.line_items or []

    return ClientInvoiceDetail(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        created_at=invoice.created_at,
        due_date=invoice.due_date,
        total=float(invoice.total),
        balance_due=float(invoice.balance_due),
        status=invoice.status,
        view_token=invoice.view_token,
        line_items=[
            ClientLineItem(
                description=item.get("description", ""),
                quantity=float(item.get("quantity", 1)),
                unit_price=float(item.get("unit_price", 0)),
                amount=float(item.get("amount", 0)),
            )
            for item in line_items
        ],
        payments=[
            ClientPaymentSummary(
                id=p.id,
                amount=float(p.amount),
                payment_date=p.payment_date,
                payment_method=p.payment_method,
            )
            for p in invoice.payments
        ],
    )


# ============ Contracts ============

@router.get("/contracts", response_model=List[ClientContractSummary])
async def list_contracts(
    status_filter: Optional[str] = None,
    view_mode: Literal["personal", "organization"] = Query("personal"),
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """List client's contracts."""
    show_org = view_mode == "organization" and contact.is_org_admin and contact.organization_id

    if show_org:
        base_filter = or_(
            Contract.contact_id == contact.id,
            Contract.organization_id == contact.organization_id,
        )
    else:
        base_filter = Contract.contact_id == contact.id

    query = select(Contract).options(selectinload(Contract.contact)).where(base_filter)

    if status_filter:
        query = query.where(Contract.status == status_filter)

    query = query.order_by(Contract.created_at.desc())

    result = await db.execute(query)

    contracts = []
    for c in result.scalars():
        contact_name = None
        if show_org and c.contact and c.contact_id != contact.id:
            contact_name = f"{c.contact.first_name} {c.contact.last_name or ''}".strip()
        contracts.append(
            ClientContractSummary(
                id=c.id,
                contract_number=c.contract_number,
                title=c.title,
                status=c.status,
                created_at=c.created_at,
                signed_at=c.signed_at,
                contact_name=contact_name,
            )
        )
    return contracts


@router.get("/contracts/{contract_id}", response_model=ClientContractDetail)
async def get_contract(
    contract_id: str,
    request: Request,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get contract detail."""
    # Log access
    await log_portal_action(
        db, contact.id, "view_contract", "contract", contract_id, get_client_ip(request)
    )
    if contact.is_org_admin and contact.organization_id:
        base_filter = or_(
            Contract.contact_id == contact.id,
            Contract.organization_id == contact.organization_id,
        )
    else:
        base_filter = Contract.contact_id == contact.id

    result = await db.execute(
        select(Contract).where(Contract.id == contract_id, base_filter)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return ClientContractDetail(
        id=contract.id,
        contract_number=contract.contract_number,
        title=contract.title,
        status=contract.status,
        created_at=contract.created_at,
        signed_at=contract.signed_at,
        content=contract.content,
        expires_at=contract.expires_at,
        view_token=contract.view_token,
    )


@router.get("/contracts/{contract_id}/pdf")
async def download_contract_pdf(
    contract_id: str,
    request: Request,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download contract as PDF."""
    # Log download
    await log_portal_action(
        db, contact.id, "download_contract_pdf", "contract", contract_id, get_client_ip(request)
    )
    if not pdf_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="PDF generation is not available.",
        )

    # Verify access
    if contact.is_org_admin and contact.organization_id:
        base_filter = or_(
            Contract.contact_id == contact.id,
            Contract.organization_id == contact.organization_id,
        )
    else:
        base_filter = Contract.contact_id == contact.id

    result = await db.execute(
        select(Contract)
        .options(
            selectinload(Contract.contact),
            selectinload(Contract.organization),
        )
        .where(Contract.id == contract_id, base_filter)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    pdf_bytes = await pdf_service.generate_contract_pdf(
        title=contract.title,
        contract_number=contract.contract_number,
        content=contract.content,
        contact_name=contract.contact.full_name if contract.contact else "Unknown",
        organization_name=contract.organization.name if contract.organization else None,
        created_at=contract.created_at,
        signer_name=contract.signer_name,
        signer_email=contract.signer_email,
        signed_at=contract.signed_at,
        signature_data=contract.signature_data,
        signer_ip=contract.signer_ip,
    )

    if pdf_bytes is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate PDF",
        )

    filename = f"{contract.contract_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ============ Bookings ============

@router.get("/bookings", response_model=List[ClientBookingSummary])
async def list_bookings(
    upcoming_only: bool = False,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """List client's bookings."""
    query = (
        select(Booking)
        .options(selectinload(Booking.booking_type))
        .where(Booking.contact_id == contact.id)
    )

    if upcoming_only:
        query = query.where(
            Booking.start_time > datetime.utcnow(),
            Booking.status == "confirmed",
        )

    query = query.order_by(Booking.start_time.desc())

    result = await db.execute(query)

    return [
        ClientBookingSummary(
            id=b.id,
            booking_type_name=b.booking_type.name if b.booking_type else "Session",
            start_time=b.start_time,
            end_time=b.end_time,
            status=b.status,
            meeting_link=b.zoom_meeting_url,
        )
        for b in result.scalars()
    ]


@router.get("/bookings/{booking_id}", response_model=ClientBookingDetail)
async def get_booking(
    booking_id: str,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get booking detail."""
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.booking_type))
        .where(Booking.id == booking_id, Booking.contact_id == contact.id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Can cancel if booking is in the future and at least 24 hours away
    can_cancel = (
        booking.status == "confirmed"
        and booking.start_time > datetime.utcnow() + timedelta(hours=24)
    )

    return ClientBookingDetail(
        id=booking.id,
        booking_type_name=booking.booking_type.name if booking.booking_type else "Session",
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        meeting_link=booking.zoom_meeting_url,
        notes=booking.notes,
        can_cancel=can_cancel,
    )


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    request: Request,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a booking."""
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.contact_id == contact.id,
        )
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != "confirmed":
        raise HTTPException(status_code=400, detail="Booking cannot be cancelled")

    if booking.start_time <= datetime.utcnow() + timedelta(hours=24):
        raise HTTPException(
            status_code=400,
            detail="Bookings must be cancelled at least 24 hours in advance",
        )

    booking.status = "cancelled"

    # Log cancellation
    await log_portal_action(
        db, contact.id, "cancel_booking", "booking", booking_id, get_client_ip(request)
    )
    await db.commit()

    return {"message": "Booking cancelled successfully"}


# ============ Projects ============

@router.get("/projects", response_model=List[ClientProjectSummary])
async def list_projects(
    view_mode: Literal["personal", "organization"] = Query("personal"),
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """List client's visible projects."""
    show_org = view_mode == "organization" and contact.is_org_admin and contact.organization_id

    if show_org:
        base_filter = or_(
            Project.contact_id == contact.id,
            Project.organization_id == contact.organization_id,
        )
    else:
        base_filter = Project.contact_id == contact.id

    result = await db.execute(
        select(Project)
        .options(selectinload(Project.tasks), selectinload(Project.contact))
        .where(base_filter, Project.client_visible == True)
        .order_by(Project.created_at.desc())
    )

    projects = []
    for project in result.scalars():
        total_tasks = len(project.tasks)
        completed_tasks = sum(1 for t in project.tasks if t.status == "completed")
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        contact_name = None
        if show_org and project.contact and project.contact_id != contact.id:
            contact_name = f"{project.contact.first_name} {project.contact.last_name or ''}".strip()

        projects.append(
            ClientProjectSummary(
                id=project.id,
                name=project.name,
                status=project.status,
                progress=progress,
                created_at=project.created_at,
                contact_name=contact_name,
            )
        )

    return projects


@router.get("/projects/{project_id}", response_model=ClientProjectDetail)
async def get_project(
    project_id: str,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get project detail with tasks."""
    if contact.is_org_admin and contact.organization_id:
        base_filter = or_(
            Project.contact_id == contact.id,
            Project.organization_id == contact.organization_id,
        )
    else:
        base_filter = Project.contact_id == contact.id

    result = await db.execute(
        select(Project)
        .options(selectinload(Project.tasks))
        .where(Project.id == project_id, base_filter, Project.client_visible == True)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    total_tasks = len(project.tasks)
    completed_tasks = sum(1 for t in project.tasks if t.status == "completed")
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Only show client-visible tasks
    visible_tasks = [t for t in project.tasks if getattr(t, "client_visible", True)]

    return ClientProjectDetail(
        id=project.id,
        name=project.name,
        status=project.status,
        progress=progress,
        created_at=project.created_at,
        description=project.description,
        tasks=[
            ClientTaskSummary(
                id=t.id,
                title=t.title,
                status=t.status,
                due_date=t.due_date,
            )
            for t in visible_tasks
        ],
    )


# ============ Profile ============

@router.get("/profile", response_model=ClientProfile)
async def get_profile(
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get client profile."""
    org_name = None
    if contact.organization_id:
        result = await db.execute(
            select(Organization).where(Organization.id == contact.organization_id)
        )
        org = result.scalar_one_or_none()
        if org:
            org_name = org.name

    return ClientProfile(
        id=contact.id,
        first_name=contact.first_name,
        last_name=contact.last_name,
        email=contact.email,
        phone=contact.phone,
        organization_name=org_name,
        is_org_admin=contact.is_org_admin,
    )


@router.put("/profile", response_model=ClientProfile)
async def update_profile(
    data: ClientProfileUpdate,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Update client profile."""
    if data.first_name is not None:
        contact.first_name = data.first_name
    if data.last_name is not None:
        contact.last_name = data.last_name
    if data.phone is not None:
        contact.phone = data.phone

    await db.commit()
    await db.refresh(contact)

    org_name = None
    if contact.organization_id:
        result = await db.execute(
            select(Organization).where(Organization.id == contact.organization_id)
        )
        org = result.scalar_one_or_none()
        if org:
            org_name = org.name

    return ClientProfile(
        id=contact.id,
        first_name=contact.first_name,
        last_name=contact.last_name,
        email=contact.email,
        phone=contact.phone,
        organization_name=org_name,
        is_org_admin=contact.is_org_admin,
    )


# ============ Sessions / Recordings ============
# NOTE: Session content (recordings, transcripts, summaries, homework) is PRIVATE
# to the individual coachee. Org admins can only see aggregate stats via /organization.

@router.get("/sessions", response_model=List[ClientSessionRecordingSummary])
async def list_sessions(
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """List client's own session recordings. Session content is private to the individual."""
    # Only show user's own sessions - no org view for session content
    result = await db.execute(
        select(FathomWebhook)
        .where(
            FathomWebhook.contact_id == contact.id,
            FathomWebhook.client_visible == True,
        )
        .order_by(FathomWebhook.recorded_at.desc())
    )

    sessions = []
    for session in result.scalars():
        sessions.append(
            ClientSessionRecordingSummary(
                id=session.id,
                meeting_title=session.meeting_title,
                recorded_at=session.recorded_at,
                duration_seconds=session.duration_seconds,
                has_recording=bool(session.recording_url),
                has_transcript=bool(session.transcript),
                has_summary=bool(session.summary),
                has_homework=bool(session.homework),
            )
        )
    return sessions


@router.get("/sessions/{session_id}", response_model=ClientSessionRecordingDetail)
async def get_session(
    session_id: str,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get session recording detail. Session content is private to the individual coachee."""
    # Only allow access to user's own sessions - session content is confidential
    result = await db.execute(
        select(FathomWebhook).where(
            FathomWebhook.id == session_id,
            FathomWebhook.contact_id == contact.id,
            FathomWebhook.client_visible == True,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Parse homework items
    homework_items = None
    if session.homework:
        homework_items = [
            ClientHomeworkItem(
                description=item.get("description", "") if isinstance(item, dict) else str(item),
                completed=item.get("completed", False) if isinstance(item, dict) else False,
            )
            for item in session.homework
        ]

    # Parse action items (convert to list of strings if needed)
    action_items = None
    if session.action_items:
        action_items = [
            item.get("description", "") if isinstance(item, dict) else str(item)
            for item in session.action_items
        ]

    return ClientSessionRecordingDetail(
        id=session.id,
        meeting_title=session.meeting_title,
        recorded_at=session.recorded_at,
        duration_seconds=session.duration_seconds,
        recording_url=session.recording_url,
        transcript=session.transcript,
        summary=session.summary,
        action_items=action_items,
        homework=homework_items,
    )


@router.put("/sessions/{session_id}/homework/{homework_index}")
async def update_homework_status(
    session_id: str,
    homework_index: int,
    completed: bool,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Mark a homework item as completed or not completed. Only the coachee can update their own homework."""
    # Only allow updating user's own homework - session content is confidential
    result = await db.execute(
        select(FathomWebhook).where(
            FathomWebhook.id == session_id,
            FathomWebhook.contact_id == contact.id,
            FathomWebhook.client_visible == True,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.homework or homework_index >= len(session.homework):
        raise HTTPException(status_code=404, detail="Homework item not found")

    # Update the homework item
    homework = list(session.homework)
    if isinstance(homework[homework_index], dict):
        homework[homework_index]["completed"] = completed
    else:
        homework[homework_index] = {"description": str(homework[homework_index]), "completed": completed}

    session.homework = homework
    await db.commit()

    return {"message": "Homework status updated"}


# ============ Organization (for Org Admins) ============

@router.get("/organization", response_model=OrgDashboardResponse)
async def get_organization_dashboard(
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get organization dashboard for org admins. Shows billing and usage stats, not session content."""
    if not contact.is_org_admin or not contact.organization_id:
        raise HTTPException(status_code=403, detail="Organization admin access required")

    # Get organization
    result = await db.execute(
        select(Organization).where(Organization.id == contact.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get all employees in org
    result = await db.execute(
        select(Contact).where(Contact.organization_id == contact.organization_id)
    )
    employees = list(result.scalars())
    employee_ids = [e.id for e in employees]

    # Billing summary - org-level invoices
    result = await db.execute(
        select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.total), 0),
            func.coalesce(func.sum(Invoice.amount_paid), 0),
            func.coalesce(func.sum(Invoice.balance_due), 0),
        ).where(Invoice.organization_id == contact.organization_id)
    )
    invoice_count, total_invoiced, total_paid, total_outstanding = result.one()

    # Usage stats - sessions for all employees (counts only, no content)
    result = await db.execute(
        select(func.count(FathomWebhook.id)).where(
            FathomWebhook.contact_id.in_(employee_ids),
            FathomWebhook.recorded_at.isnot(None),
        )
    )
    total_sessions_completed = result.scalar() or 0

    # Upcoming bookings for all employees
    result = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.contact_id.in_(employee_ids),
            Booking.status == "confirmed",
            Booking.start_time > datetime.utcnow(),
        )
    )
    total_sessions_upcoming = result.scalar() or 0

    # Total coaching hours
    result = await db.execute(
        select(func.coalesce(func.sum(FathomWebhook.duration_seconds), 0)).where(
            FathomWebhook.contact_id.in_(employee_ids),
        )
    )
    total_seconds = result.scalar() or 0
    total_coaching_hours = round(total_seconds / 3600, 1)

    # Employees with at least one session
    result = await db.execute(
        select(func.count(func.distinct(FathomWebhook.contact_id))).where(
            FathomWebhook.contact_id.in_(employee_ids),
        )
    )
    employees_with_sessions = result.scalar() or 0

    # Recent org invoices
    result = await db.execute(
        select(Invoice)
        .where(Invoice.organization_id == contact.organization_id)
        .order_by(Invoice.created_at.desc())
        .limit(5)
    )
    recent_invoices = [
        ClientInvoiceSummary(
            id=inv.id,
            invoice_number=inv.invoice_number,
            created_at=inv.created_at,
            due_date=inv.due_date,
            total=float(inv.total),
            balance_due=float(inv.balance_due),
            status=inv.status,
        )
        for inv in result.scalars()
    ]

    # Pending contracts count
    result = await db.execute(
        select(func.count(Contract.id)).where(
            Contract.organization_id == contact.organization_id,
            Contract.status.in_(["sent", "viewed"]),
        )
    )
    pending_contracts = result.scalar() or 0

    return OrgDashboardResponse(
        organization_name=org.name,
        organization_id=org.id,
        billing=OrgBillingSummary(
            total_invoiced=float(total_invoiced),
            total_paid=float(total_paid),
            total_outstanding=float(total_outstanding),
            invoice_count=invoice_count,
        ),
        usage=OrgUsageStats(
            total_employees=len(employees),
            employees_with_sessions=employees_with_sessions,
            total_sessions_completed=total_sessions_completed,
            total_sessions_upcoming=total_sessions_upcoming,
            total_coaching_hours=total_coaching_hours,
        ),
        recent_invoices=recent_invoices,
        pending_contracts=pending_contracts,
    )


@router.get("/organization/employees", response_model=List[OrgEmployeeSummary])
async def get_organization_employees(
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get employee roster with usage stats (no session content)."""
    if not contact.is_org_admin or not contact.organization_id:
        raise HTTPException(status_code=403, detail="Organization admin access required")

    # Get all employees in org
    result = await db.execute(
        select(Contact).where(Contact.organization_id == contact.organization_id)
    )
    employees = list(result.scalars())

    employee_summaries = []
    for emp in employees:
        # Count completed sessions
        result = await db.execute(
            select(func.count(FathomWebhook.id)).where(
                FathomWebhook.contact_id == emp.id,
                FathomWebhook.recorded_at.isnot(None),
            )
        )
        sessions_completed = result.scalar() or 0

        # Count upcoming bookings
        result = await db.execute(
            select(func.count(Booking.id)).where(
                Booking.contact_id == emp.id,
                Booking.status == "confirmed",
                Booking.start_time > datetime.utcnow(),
            )
        )
        sessions_upcoming = result.scalar() or 0

        # Last session date
        result = await db.execute(
            select(FathomWebhook.recorded_at)
            .where(FathomWebhook.contact_id == emp.id)
            .order_by(FathomWebhook.recorded_at.desc())
            .limit(1)
        )
        last_session = result.scalar_one_or_none()

        employee_summaries.append(
            OrgEmployeeSummary(
                id=emp.id,
                first_name=emp.first_name,
                last_name=emp.last_name,
                email=emp.email,
                sessions_completed=sessions_completed,
                sessions_upcoming=sessions_upcoming,
                last_session_date=last_session,
            )
        )

    return employee_summaries


# ============ Resources / Content ============

@router.get("/resources", response_model=List[ClientContentSummary])
async def list_resources(
    category: Optional[str] = None,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    List all content/resources available to the client.

    Content can be assigned to:
    - Specific contact (personal coaching materials)
    - Organization (org-wide resources)
    - No assignment (general resources for all)
    """
    now = datetime.utcnow()

    # Build filter for content the client can access
    filters = [
        ClientContent.is_active == True,
    ]

    # Content accessible to this client:
    # 1. Assigned specifically to them
    # 2. Assigned to their organization (if they belong to one)
    # 3. Not assigned to anyone (general content)
    access_conditions = [
        ClientContent.contact_id == contact.id,
        (ClientContent.contact_id == None) & (ClientContent.organization_id == None) & (ClientContent.project_id == None),
    ]

    if contact.organization_id:
        access_conditions.append(ClientContent.organization_id == contact.organization_id)

    filters.append(or_(*access_conditions))

    # Filter by category if specified
    if category:
        filters.append(ClientContent.category == category)

    # Query content
    result = await db.execute(
        select(ClientContent)
        .where(*filters)
        .order_by(ClientContent.category, ClientContent.sort_order, ClientContent.created_at.desc())
    )
    contents = result.scalars().all()

    return [
        ClientContentSummary(
            id=c.id,
            title=c.title,
            description=c.description,
            content_type=c.content_type,
            category=c.category,
            file_name=c.file_name,
            file_size=c.file_size,
            external_url=c.external_url,
            release_date=c.release_date,
            is_released=c.is_released,
            created_at=c.created_at,
        )
        for c in contents
    ]


@router.get("/resources/{content_id}", response_model=ClientContentDetail)
async def get_resource(
    content_id: str,
    request: Request,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get content detail with download URL."""
    # Build access filter
    access_conditions = [
        ClientContent.contact_id == contact.id,
        (ClientContent.contact_id == None) & (ClientContent.organization_id == None) & (ClientContent.project_id == None),
    ]

    if contact.organization_id:
        access_conditions.append(ClientContent.organization_id == contact.organization_id)

    result = await db.execute(
        select(ClientContent).where(
            ClientContent.id == content_id,
            ClientContent.is_active == True,
            or_(*access_conditions),
        )
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Check if content is released
    if not content.is_released:
        raise HTTPException(
            status_code=403,
            detail=f"This resource will be available on {content.release_date.strftime('%B %d, %Y')}"
        )

    # Log access
    await log_portal_action(
        db, contact.id, "view_resource", "content", content_id, get_client_ip(request)
    )

    return ClientContentDetail(
        id=content.id,
        title=content.title,
        description=content.description,
        content_type=content.content_type,
        category=content.category,
        file_name=content.file_name,
        file_size=content.file_size,
        file_url=content.file_url,
        external_url=content.external_url,
        mime_type=content.mime_type,
        release_date=content.release_date,
        is_released=content.is_released,
        created_at=content.created_at,
    )


@router.get("/resources/categories/list")
async def list_resource_categories(
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get list of content categories available to the client."""
    # Build access filter
    access_conditions = [
        ClientContent.contact_id == contact.id,
        (ClientContent.contact_id == None) & (ClientContent.organization_id == None) & (ClientContent.project_id == None),
    ]

    if contact.organization_id:
        access_conditions.append(ClientContent.organization_id == contact.organization_id)

    result = await db.execute(
        select(ClientContent.category)
        .where(
            ClientContent.is_active == True,
            ClientContent.category != None,
            or_(*access_conditions),
        )
        .distinct()
        .order_by(ClientContent.category)
    )
    categories = [row[0] for row in result.fetchall()]

    return {"categories": categories}


# ============================================================================
# Notes Endpoints
# ============================================================================

@router.get("/notes", response_model=List[ClientNoteResponse])
async def list_notes(
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get all notes for the current client (both directions)."""
    result = await db.execute(
        select(ClientNote)
        .where(ClientNote.contact_id == contact.id)
        .order_by(ClientNote.created_at.asc())
    )
    notes = result.scalars().all()

    return [
        ClientNoteResponse(
            id=note.id,
            content=note.content,
            direction=note.direction,
            is_read=note.is_read,
            created_at=note.created_at,
        )
        for note in notes
    ]


@router.post("/notes", response_model=ClientNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    data: ClientNoteCreate,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Create a note to the coach."""
    note = ClientNote(
        contact_id=contact.id,
        content=data.content,
        direction="to_coach",
        is_read=False,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    # Send email notification to coach
    settings = get_settings()
    if settings.coach_email:
        client_name = f"{contact.first_name} {contact.last_name or ''}".strip()
        notes_url = f"{settings.frontend_url}/notes"
        try:
            await email_service.send_note_to_coach_notification(
                coach_email=settings.coach_email,
                client_name=client_name,
                note_content=data.content,
                notes_url=notes_url,
            )
        except Exception as e:
            # Log but don't fail the request if email fails
            import logging
            logging.getLogger(__name__).error(f"Failed to send note notification email: {e}")

    return ClientNoteResponse(
        id=note.id,
        content=note.content,
        direction=note.direction,
        is_read=note.is_read,
        created_at=note.created_at,
    )


@router.put("/notes/{note_id}/read", response_model=ClientNoteResponse)
async def mark_note_read(
    note_id: str,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Mark a coach's note as read."""
    result = await db.execute(
        select(ClientNote).where(
            ClientNote.id == note_id,
            ClientNote.contact_id == contact.id,
            ClientNote.direction == "to_client",  # Only mark coach's notes as read
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    note.is_read = True
    note.read_at = datetime.utcnow()
    await db.commit()
    await db.refresh(note)

    return ClientNoteResponse(
        id=note.id,
        content=note.content,
        direction=note.direction,
        is_read=note.is_read,
        created_at=note.created_at,
    )


@router.get("/notes/unread-count")
async def get_unread_count(
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get count of unread notes from coach."""
    count = await db.scalar(
        select(func.count(ClientNote.id)).where(
            ClientNote.contact_id == contact.id,
            ClientNote.direction == "to_client",
            ClientNote.is_read == False,
        )
    )
    return {"count": count or 0}


# ============================================================================
# Action Items Endpoints
# ============================================================================

@router.get("/action-items", response_model=List[ClientActionItemResponse])
async def list_action_items(
    status_filter: Optional[str] = Query(None, alias="status"),
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get all action items for the current client."""
    query = select(ClientActionItem).where(ClientActionItem.contact_id == contact.id)

    if status_filter:
        query = query.where(ClientActionItem.status == status_filter)

    query = query.order_by(
        ClientActionItem.due_date.asc().nullslast(),
        ClientActionItem.created_at.desc(),
    )

    result = await db.execute(query)
    items = result.scalars().all()

    return [
        ClientActionItemResponse(
            id=item.id,
            title=item.title,
            description=item.description,
            due_date=item.due_date,
            priority=item.priority,
            status=item.status,
            completed_at=item.completed_at,
            created_at=item.created_at,
        )
        for item in items
    ]


@router.put("/action-items/{item_id}/status", response_model=ClientActionItemResponse)
async def update_action_item_status(
    item_id: str,
    data: ClientActionItemStatusUpdate,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Update action item status (complete, skip, or mark in progress)."""
    result = await db.execute(
        select(ClientActionItem).where(
            ClientActionItem.id == item_id,
            ClientActionItem.contact_id == contact.id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action item not found",
        )

    item.status = data.status
    if data.status == "completed":
        item.completed_at = datetime.utcnow()
    elif data.status in ["pending", "in_progress"]:
        item.completed_at = None

    await db.commit()
    await db.refresh(item)

    return ClientActionItemResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        due_date=item.due_date,
        priority=item.priority,
        status=item.status,
        completed_at=item.completed_at,
        created_at=item.created_at,
    )


@router.get("/action-items/pending-count")
async def get_pending_action_items_count(
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get count of pending action items."""
    count = await db.scalar(
        select(func.count(ClientActionItem.id)).where(
            ClientActionItem.contact_id == contact.id,
            ClientActionItem.status.in_(["pending", "in_progress"]),
        )
    )
    return {"count": count or 0}


# ============== Goals ============== #

@router.get("/goals", response_model=List[ClientGoalResponse])
async def list_goals(
    status_filter: Optional[str] = Query(None, alias="status"),
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get all goals for the current client."""
    query = (
        select(ClientGoal)
        .options(selectinload(ClientGoal.milestones))
        .where(ClientGoal.contact_id == contact.id)
    )

    if status_filter:
        query = query.where(ClientGoal.status == status_filter)

    query = query.order_by(ClientGoal.created_at.desc())

    result = await db.execute(query)
    goals = result.scalars().unique().all()

    return [
        ClientGoalResponse(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            category=goal.category,
            status=goal.status,
            target_date=goal.target_date,
            progress_percent=goal.progress_percent,
            milestones=[
                MilestoneResponse(
                    id=m.id,
                    goal_id=m.goal_id,
                    title=m.title,
                    description=m.description,
                    target_date=m.target_date,
                    is_completed=m.is_completed,
                    completed_at=m.completed_at,
                    sort_order=m.sort_order,
                    created_at=m.created_at,
                )
                for m in goal.milestones
            ],
            created_at=goal.created_at,
        )
        for goal in goals
    ]


@router.get("/goals/{goal_id}", response_model=ClientGoalResponse)
async def get_goal(
    goal_id: str,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific goal with milestones."""
    result = await db.execute(
        select(ClientGoal)
        .options(selectinload(ClientGoal.milestones))
        .where(ClientGoal.id == goal_id, ClientGoal.contact_id == contact.id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    return ClientGoalResponse(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        category=goal.category,
        status=goal.status,
        target_date=goal.target_date,
        progress_percent=goal.progress_percent,
        milestones=[
            MilestoneResponse(
                id=m.id,
                goal_id=m.goal_id,
                title=m.title,
                description=m.description,
                target_date=m.target_date,
                is_completed=m.is_completed,
                completed_at=m.completed_at,
                sort_order=m.sort_order,
                created_at=m.created_at,
            )
            for m in goal.milestones
        ],
        created_at=goal.created_at,
    )


@router.put("/goals/{goal_id}/milestones/{milestone_id}/complete", response_model=MilestoneResponse)
async def complete_milestone(
    goal_id: str,
    milestone_id: str,
    data: ClientMilestoneComplete,
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Mark a milestone as complete or incomplete."""
    # Verify the goal belongs to this client
    goal_result = await db.execute(
        select(ClientGoal).where(
            ClientGoal.id == goal_id,
            ClientGoal.contact_id == contact.id,
        )
    )
    goal = goal_result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    # Get the milestone
    result = await db.execute(
        select(GoalMilestone).where(
            GoalMilestone.id == milestone_id,
            GoalMilestone.goal_id == goal_id,
        )
    )
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found",
        )

    milestone.is_completed = data.is_completed
    if data.is_completed:
        milestone.completed_at = datetime.utcnow()
    else:
        milestone.completed_at = None

    await db.commit()
    await db.refresh(milestone)

    return MilestoneResponse(
        id=milestone.id,
        goal_id=milestone.goal_id,
        title=milestone.title,
        description=milestone.description,
        target_date=milestone.target_date,
        is_completed=milestone.is_completed,
        completed_at=milestone.completed_at,
        sort_order=milestone.sort_order,
        created_at=milestone.created_at,
    )


@router.get("/goals/stats/summary")
async def get_goals_stats(
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get goal statistics for the client."""
    active_count = await db.scalar(
        select(func.count(ClientGoal.id)).where(
            ClientGoal.contact_id == contact.id,
            ClientGoal.status == "active",
        )
    )
    completed_count = await db.scalar(
        select(func.count(ClientGoal.id)).where(
            ClientGoal.contact_id == contact.id,
            ClientGoal.status == "completed",
        )
    )
    return {
        "active_goals": active_count or 0,
        "completed_goals": completed_count or 0,
    }


# ============== Timeline ============== #

@router.get("/timeline")
async def get_timeline(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    event_types: Optional[str] = Query(None),  # comma-separated: goals,sessions,action_items,notes,contracts
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get unified timeline of client journey events."""
    from datetime import datetime as dt

    events = []

    # Parse date filters
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = dt.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = dt.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        except ValueError:
            pass

    # Parse event types filter
    types = set()
    if event_types:
        types = set(event_types.split(","))
    include_all = len(types) == 0

    # 1. Sessions (Bookings)
    if include_all or "sessions" in types:
        booking_query = select(Booking).where(Booking.contact_id == contact.id)
        if start_dt:
            booking_query = booking_query.where(Booking.start_time >= start_dt)
        if end_dt:
            booking_query = booking_query.where(Booking.start_time <= end_dt)
        booking_result = await db.execute(booking_query)
        bookings = booking_result.scalars().all()

        for b in bookings:
            event_type = "session_completed" if b.status == "completed" else "session_scheduled"
            if b.status == "cancelled":
                event_type = "session_cancelled"
            events.append({
                "id": f"booking_{b.id}",
                "type": event_type,
                "title": f"Session: {b.notes or 'Coaching Session'}",
                "description": f"{b.status.title()} session" if b.notes else None,
                "date": b.start_time.isoformat(),
                "icon": "calendar" if event_type == "session_scheduled" else "check-circle" if event_type == "session_completed" else "x-circle",
                "color": "blue" if event_type == "session_scheduled" else "green" if event_type == "session_completed" else "gray",
            })

    # 2. Goals and Milestones
    if include_all or "goals" in types:
        goal_query = (
            select(ClientGoal)
            .options(selectinload(ClientGoal.milestones))
            .where(ClientGoal.contact_id == contact.id)
        )
        goal_result = await db.execute(goal_query)
        goals = goal_result.scalars().unique().all()

        for g in goals:
            # Goal created
            if (not start_dt or g.created_at >= start_dt) and (not end_dt or g.created_at <= end_dt):
                events.append({
                    "id": f"goal_created_{g.id}",
                    "type": "goal_created",
                    "title": f"Goal set: {g.title}",
                    "description": g.description,
                    "date": g.created_at.isoformat(),
                    "icon": "target",
                    "color": "purple",
                })

            # Goal completed
            if g.status == "completed" and g.completed_at:
                if (not start_dt or g.completed_at >= start_dt) and (not end_dt or g.completed_at <= end_dt):
                    events.append({
                        "id": f"goal_completed_{g.id}",
                        "type": "goal_completed",
                        "title": f"Goal achieved: {g.title}",
                        "description": None,
                        "date": g.completed_at.isoformat(),
                        "icon": "trophy",
                        "color": "gold",
                    })

            # Milestones completed
            for m in g.milestones:
                if m.is_completed and m.completed_at:
                    if (not start_dt or m.completed_at >= start_dt) and (not end_dt or m.completed_at <= end_dt):
                        events.append({
                            "id": f"milestone_{m.id}",
                            "type": "milestone_completed",
                            "title": f"Milestone: {m.title}",
                            "description": f"Progress on '{g.title}'",
                            "date": m.completed_at.isoformat(),
                            "icon": "check-circle",
                            "color": "green",
                        })

    # 3. Action Items
    if include_all or "action_items" in types:
        action_query = select(ClientActionItem).where(ClientActionItem.contact_id == contact.id)
        action_result = await db.execute(action_query)
        action_items = action_result.scalars().all()

        for a in action_items:
            # Action item completed
            if a.status == "completed" and a.completed_at:
                if (not start_dt or a.completed_at >= start_dt) and (not end_dt or a.completed_at <= end_dt):
                    events.append({
                        "id": f"action_completed_{a.id}",
                        "type": "action_completed",
                        "title": f"Completed: {a.title}",
                        "description": None,
                        "date": a.completed_at.isoformat(),
                        "icon": "check-square",
                        "color": "green",
                    })

    # 4. Notes/Messages
    if include_all or "notes" in types:
        note_query = select(ClientNote).where(ClientNote.contact_id == contact.id)
        if start_dt:
            note_query = note_query.where(ClientNote.created_at >= start_dt)
        if end_dt:
            note_query = note_query.where(ClientNote.created_at <= end_dt)
        note_result = await db.execute(note_query)
        notes = note_result.scalars().all()

        for n in notes:
            direction_text = "Sent message" if n.direction == "to_coach" else "Received message"
            events.append({
                "id": f"note_{n.id}",
                "type": "message",
                "title": direction_text,
                "description": n.content[:100] + "..." if len(n.content) > 100 else n.content,
                "date": n.created_at.isoformat(),
                "icon": "message-square",
                "color": "blue" if n.direction == "to_coach" else "gray",
            })

    # 5. Contracts
    if include_all or "contracts" in types:
        contract_query = select(Contract).where(
            Contract.contact_id == contact.id,
            Contract.status == "signed",
        )
        contract_result = await db.execute(contract_query)
        contracts = contract_result.scalars().all()

        for c in contracts:
            if c.signed_at:
                if (not start_dt or c.signed_at >= start_dt) and (not end_dt or c.signed_at <= end_dt):
                    events.append({
                        "id": f"contract_{c.id}",
                        "type": "contract_signed",
                        "title": f"Contract signed: {c.title}",
                        "description": None,
                        "date": c.signed_at.isoformat(),
                        "icon": "file-check",
                        "color": "green",
                    })

    # Sort by date descending (most recent first)
    events.sort(key=lambda x: x["date"], reverse=True)

    return {"events": events}


# ============ Onboarding Assessment ============


@router.get("/onboarding-assessment")
async def get_onboarding_assessment(
    contact: Contact = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the client's onboarding assessment.
    Returns null if no assessment exists.
    """
    result = await db.execute(
        select(OnboardingAssessment).where(
            OnboardingAssessment.contact_id == contact.id
        )
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        return None

    return OnboardingAssessmentResponse.model_validate(assessment)
