"""
Extraction router - AI-powered invoice extraction from Fathom transcripts.
"""
from datetime import date, datetime, timedelta
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.fathom_webhook import FathomWebhook
from app.models.fathom_extraction import FathomExtraction
from app.models.contact import Contact
from app.models.invoice import Invoice
from app.services.ai_extraction_service import ai_extraction_service
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/extractions", tags=["Extractions"])


# ============ Schemas ============

class ExtractionCreate(BaseModel):
    """Request to process a Fathom webhook."""
    webhook_id: str


class ExtractionResponse(BaseModel):
    """Extraction response."""
    id: str
    fathom_webhook_id: str
    contact_id: Optional[str]
    extracted_data: dict
    confidence_scores: dict
    confidence_level: str
    status: str
    draft_invoice_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractionListResponse(BaseModel):
    """List of extractions with pagination."""
    items: list[ExtractionResponse]
    total: int
    pending_count: int
    approved_count: int


class ExtractionReview(BaseModel):
    """Review/approve an extraction."""
    action: str  # "approve", "reject", "edit"
    corrections: Optional[list[dict]] = None  # [{field, original, corrected}]
    notes: Optional[str] = None


class WebhookListResponse(BaseModel):
    """List of pending webhooks."""
    id: str
    recording_id: Optional[str]
    meeting_title: Optional[str]
    attendees: Optional[list]
    duration_seconds: Optional[int]
    recorded_at: Optional[datetime]
    processing_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractionStats(BaseModel):
    """Stats for the extraction dashboard."""
    pending_webhooks: int
    pending_extractions: int
    approved_today: int
    total_extracted_value: float


# ============ Endpoints ============

@router.get("/stats", response_model=ExtractionStats)
async def get_extraction_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractionStats:
    """Get extraction statistics."""
    # Pending webhooks
    pending_webhooks = await db.execute(
        select(func.count(FathomWebhook.id)).where(
            FathomWebhook.processing_status == "pending"
        )
    )

    # Pending extractions
    pending_extractions = await db.execute(
        select(func.count(FathomExtraction.id)).where(
            FathomExtraction.status == "pending"
        )
    )

    # Approved today
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    approved_today = await db.execute(
        select(func.count(FathomExtraction.id)).where(
            FathomExtraction.status == "approved",
            FathomExtraction.reviewed_at >= today_start,
        )
    )

    # Total value of approved extractions with invoices
    total_value = await db.execute(
        select(func.sum(Invoice.total)).join(
            FathomExtraction, FathomExtraction.draft_invoice_id == Invoice.id
        ).where(FathomExtraction.status == "approved")
    )

    return ExtractionStats(
        pending_webhooks=pending_webhooks.scalar() or 0,
        pending_extractions=pending_extractions.scalar() or 0,
        approved_today=approved_today.scalar() or 0,
        total_extracted_value=float(total_value.scalar() or 0),
    )


@router.get("/webhooks", response_model=list[WebhookListResponse])
async def list_pending_webhooks(
    status_filter: str = "pending",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WebhookListResponse]:
    """List Fathom webhooks by status."""
    query = select(FathomWebhook).order_by(FathomWebhook.created_at.desc()).limit(limit)

    if status_filter != "all":
        query = query.where(FathomWebhook.processing_status == status_filter)

    result = await db.execute(query)
    webhooks = result.scalars().all()

    return [WebhookListResponse.model_validate(w) for w in webhooks]


@router.post("/process/{webhook_id}", response_model=ExtractionResponse)
async def process_webhook(
    webhook_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractionResponse:
    """Process a Fathom webhook and extract invoice data."""
    # Get webhook
    result = await db.execute(
        select(FathomWebhook).where(FathomWebhook.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if not webhook.transcript:
        raise HTTPException(status_code=400, detail="Webhook has no transcript")

    # Check if already processed
    existing = await db.execute(
        select(FathomExtraction).where(
            FathomExtraction.fathom_webhook_id == webhook_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Webhook already processed")

    # Update webhook status
    webhook.processing_status = "processing"
    await db.commit()

    # Run AI extraction
    extraction_result = await ai_extraction_service.extract_from_transcript(
        transcript=webhook.transcript,
        meeting_title=webhook.meeting_title,
        attendees=webhook.attendees,
    )

    if extraction_result.get("error"):
        webhook.processing_status = "failed"
        await db.commit()
        raise HTTPException(
            status_code=500,
            detail=extraction_result["error"],
        )

    extracted_data = extraction_result.get("extraction", {})
    confidence_scores = extraction_result.get("confidence", {})

    # Try to match contact by email
    contact_id = None
    client_email = extracted_data.get("client_email")
    if client_email:
        contact_result = await db.execute(
            select(Contact).where(Contact.email == client_email)
        )
        contact = contact_result.scalar_one_or_none()
        if contact:
            contact_id = contact.id

    # Create extraction record
    extraction = FathomExtraction(
        fathom_webhook_id=webhook_id,
        contact_id=contact_id,
        extracted_data=extracted_data,
        confidence_scores=confidence_scores,
        status="pending",
    )
    db.add(extraction)

    # Update webhook status
    webhook.processing_status = "completed"
    webhook.processed_at = datetime.now()

    await db.commit()
    await db.refresh(extraction)

    return ExtractionResponse(
        id=extraction.id,
        fathom_webhook_id=extraction.fathom_webhook_id,
        contact_id=extraction.contact_id,
        extracted_data=extraction.extracted_data,
        confidence_scores=extraction.confidence_scores,
        confidence_level=extraction.get_confidence_level(),
        status=extraction.status,
        draft_invoice_id=extraction.draft_invoice_id,
        created_at=extraction.created_at,
    )


@router.get("", response_model=ExtractionListResponse)
async def list_extractions(
    status_filter: str = "all",
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractionListResponse:
    """List extractions with optional status filter."""
    query = select(FathomExtraction).order_by(
        FathomExtraction.created_at.desc()
    ).offset(offset).limit(limit)

    if status_filter != "all":
        query = query.where(FathomExtraction.status == status_filter)

    result = await db.execute(query)
    extractions = result.scalars().all()

    # Get counts
    total = await db.execute(select(func.count(FathomExtraction.id)))
    pending = await db.execute(
        select(func.count(FathomExtraction.id)).where(
            FathomExtraction.status == "pending"
        )
    )
    approved = await db.execute(
        select(func.count(FathomExtraction.id)).where(
            FathomExtraction.status == "approved"
        )
    )

    return ExtractionListResponse(
        items=[
            ExtractionResponse(
                id=e.id,
                fathom_webhook_id=e.fathom_webhook_id,
                contact_id=e.contact_id,
                extracted_data=e.extracted_data,
                confidence_scores=e.confidence_scores,
                confidence_level=e.get_confidence_level(),
                status=e.status,
                draft_invoice_id=e.draft_invoice_id,
                created_at=e.created_at,
            )
            for e in extractions
        ],
        total=total.scalar() or 0,
        pending_count=pending.scalar() or 0,
        approved_count=approved.scalar() or 0,
    )


@router.get("/{extraction_id}", response_model=ExtractionResponse)
async def get_extraction(
    extraction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractionResponse:
    """Get a single extraction with details."""
    result = await db.execute(
        select(FathomExtraction).where(FathomExtraction.id == extraction_id)
    )
    extraction = result.scalar_one_or_none()

    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")

    return ExtractionResponse(
        id=extraction.id,
        fathom_webhook_id=extraction.fathom_webhook_id,
        contact_id=extraction.contact_id,
        extracted_data=extraction.extracted_data,
        confidence_scores=extraction.confidence_scores,
        confidence_level=extraction.get_confidence_level(),
        status=extraction.status,
        draft_invoice_id=extraction.draft_invoice_id,
        created_at=extraction.created_at,
    )


@router.post("/{extraction_id}/review")
async def review_extraction(
    extraction_id: str,
    review: ExtractionReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Review and approve/reject an extraction."""
    result = await db.execute(
        select(FathomExtraction).where(FathomExtraction.id == extraction_id)
    )
    extraction = result.scalar_one_or_none()

    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")

    if extraction.status != "pending":
        raise HTTPException(status_code=400, detail="Extraction already reviewed")

    if review.action == "approve":
        extraction.status = "approved"

        # Create draft invoice if billable
        if extraction.extracted_data.get("is_billable"):
            await _create_draft_invoice(db, extraction)

    elif review.action == "reject":
        extraction.status = "rejected"

    elif review.action == "edit":
        # Apply corrections
        if review.corrections:
            for correction in review.corrections:
                extraction.add_correction(
                    field=correction.get("field", ""),
                    original=correction.get("original"),
                    corrected=correction.get("corrected"),
                )
                # Update extracted_data with correction
                if correction.get("field") and "corrected" in correction:
                    extraction.extracted_data[correction["field"]] = correction["corrected"]

        extraction.status = "approved"

        # Create draft invoice with corrected data
        if extraction.extracted_data.get("is_billable"):
            await _create_draft_invoice(db, extraction)

    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    extraction.reviewed_at = datetime.now()
    extraction.reviewed_by = current_user.id
    extraction.review_notes = review.notes

    await db.commit()
    await db.refresh(extraction)

    return {
        "status": "success",
        "extraction_status": extraction.status,
        "draft_invoice_id": extraction.draft_invoice_id,
    }


@router.post("/{extraction_id}/create-invoice")
async def create_invoice_from_extraction(
    extraction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a draft invoice from an approved extraction."""
    result = await db.execute(
        select(FathomExtraction).where(FathomExtraction.id == extraction_id)
    )
    extraction = result.scalar_one_or_none()

    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")

    if extraction.draft_invoice_id:
        raise HTTPException(status_code=400, detail="Invoice already created")

    await _create_draft_invoice(db, extraction)
    await db.commit()
    await db.refresh(extraction)

    return {
        "status": "success",
        "invoice_id": extraction.draft_invoice_id,
    }


async def _create_draft_invoice(db: AsyncSession, extraction: FathomExtraction) -> None:
    """Create a draft invoice from extraction data."""
    data = extraction.extracted_data

    # Build line items
    line_items = ai_extraction_service.build_invoice_line_items(data)

    if not line_items:
        return

    # Calculate totals
    subtotal = sum(item["quantity"] * item["unit_price"] for item in line_items)

    # Generate invoice number
    from app.services.invoice_service import InvoiceService
    invoice_service = InvoiceService(db)
    invoice_number = await invoice_service.generate_invoice_number()

    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_number,
        contact_id=extraction.contact_id,
        line_items=[
            {
                "description": item["description"],
                "quantity": float(item["quantity"]),
                "unit_price": float(item["unit_price"]),
                "amount": float(item["quantity"] * item["unit_price"]),
                "service_type": item.get("service_type", "other"),
            }
            for item in line_items
        ],
        subtotal=Decimal(str(subtotal)),
        total=Decimal(str(subtotal)),
        balance_due=Decimal(str(subtotal)),
        payment_terms="net_30",
        due_date=date.today() + timedelta(days=30),
        status="draft",
        notes=f"Auto-generated from call: {data.get('key_topics', [])}",
    )
    db.add(invoice)
    await db.flush()

    extraction.draft_invoice_id = invoice.id
