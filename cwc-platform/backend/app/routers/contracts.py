"""
Contract management router.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.contract import Contract
from app.models.contract_template import ContractTemplate
from app.models.signature_audit_log import SignatureAuditLog
from app.models.contact import Contact
from app.models.organization import Organization
from app.models.invoice import Invoice
from app.schemas.contract import (
    ContractCreate,
    ContractUpdate,
    ContractRead,
    ContractList,
    ContractDetail,
    ContractSend,
    ContractVoid,
    ContractStats,
    SignatureAuditLogRead,
)
from app.services.contract_service import ContractService
from app.services.email_service import email_service
from app.services.pdf_service import pdf_service

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


@router.get("", response_model=list[ContractList])
async def list_contracts(
    status: Optional[str] = Query(None, description="Filter by status"),
    contact_id: Optional[str] = Query(None, description="Filter by contact"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    search: Optional[str] = Query(None, description="Search contract number or title"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[ContractList]:
    """List all contracts with optional filters."""
    query = select(Contract).options(
        selectinload(Contract.contact),
        selectinload(Contract.organization),
    )

    # Apply filters
    conditions = []
    if status:
        conditions.append(Contract.status == status)
    if contact_id:
        conditions.append(Contract.contact_id == contact_id)
    if organization_id:
        conditions.append(Contract.organization_id == organization_id)

    if conditions:
        query = query.where(and_(*conditions))

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Contract.contract_number.ilike(search_term),
                Contract.title.ilike(search_term),
            )
        )

    query = query.order_by(Contract.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    contracts = result.scalars().all()

    return [
        ContractList(
            id=c.id,
            contract_number=c.contract_number,
            title=c.title,
            contact_id=c.contact_id,
            contact_name=c.contact.full_name if c.contact else None,
            organization_name=c.organization.name if c.organization else None,
            status=c.status,
            sent_at=c.sent_at,
            signed_at=c.signed_at,
            expires_at=c.expires_at,
            created_at=c.created_at,
        )
        for c in contracts
    ]


@router.get("/stats", response_model=ContractStats)
async def get_contract_stats(
    db: AsyncSession = Depends(get_db),
) -> ContractStats:
    """Get contract statistics for dashboard."""
    service = ContractService(db)
    stats = await service.get_stats()
    return ContractStats(**stats)


@router.get("/{contract_id}", response_model=ContractDetail)
async def get_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
) -> ContractDetail:
    """Get a specific contract with full details."""
    result = await db.execute(
        select(Contract)
        .options(
            selectinload(Contract.contact),
            selectinload(Contract.organization),
            selectinload(Contract.template),
            selectinload(Contract.linked_invoice),
            selectinload(Contract.audit_logs),
        )
        .where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return ContractDetail(
        id=contract.id,
        contract_number=contract.contract_number,
        template_id=contract.template_id,
        contact_id=contract.contact_id,
        organization_id=contract.organization_id,
        title=contract.title,
        content=contract.content,
        status=contract.status,
        sent_at=contract.sent_at,
        viewed_at=contract.viewed_at,
        signed_at=contract.signed_at,
        expires_at=contract.expires_at,
        declined_at=contract.declined_at,
        decline_reason=contract.decline_reason,
        signer_name=contract.signer_name,
        signer_email=contract.signer_email,
        signature_type=contract.signature_type,
        content_hash=contract.content_hash,
        linked_invoice_id=contract.linked_invoice_id,
        view_token=contract.view_token,
        notes=contract.notes,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        contact_name=contract.contact.full_name if contract.contact else None,
        contact_email=contract.contact.email if contract.contact else None,
        organization_name=contract.organization.name if contract.organization else None,
        template_name=contract.template.name if contract.template else None,
        linked_invoice_number=contract.linked_invoice.invoice_number if contract.linked_invoice else None,
        audit_logs=[SignatureAuditLogRead.model_validate(log) for log in contract.audit_logs],
    )


@router.post("", response_model=ContractRead, status_code=201)
async def create_contract(
    data: ContractCreate,
    db: AsyncSession = Depends(get_db),
) -> ContractRead:
    """Create a new contract (from template or from scratch)."""
    service = ContractService(db)

    # Generate contract number
    contract_number = await service.generate_contract_number()

    # Build content
    content = ""
    template = None

    if data.template_id:
        # Create from template
        result = await db.execute(
            select(ContractTemplate).where(ContractTemplate.id == data.template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Build merge data
        auto_merge_data = await service.build_auto_merge_data(
            contact_id=data.contact_id,
            organization_id=data.organization_id,
            contract_number=contract_number,
        )

        # Combine auto and custom merge data
        merge_data = {**auto_merge_data, **(data.merge_data or {})}

        # Render content
        content = service.render_content(template.content, merge_data)
    elif data.content:
        content = data.content
    else:
        raise HTTPException(
            status_code=400,
            detail="Either template_id or content must be provided",
        )

    # Create contract
    contract = Contract(
        contract_number=contract_number,
        template_id=data.template_id,
        contact_id=data.contact_id,
        organization_id=data.organization_id,
        title=data.title,
        content=content,
        notes=data.notes,
        linked_invoice_id=data.linked_invoice_id,
        status="draft",
    )

    db.add(contract)
    await db.flush()

    # Log creation
    await service.log_action(
        contract_id=contract.id,
        action="created",
        details={"template_id": data.template_id},
    )

    await db.commit()
    await db.refresh(contract)

    return ContractRead.model_validate(contract)


@router.put("/{contract_id}", response_model=ContractRead)
async def update_contract(
    contract_id: str,
    data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
) -> ContractRead:
    """Update a draft contract."""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if contract.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft contracts can be edited",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)

    await db.commit()
    await db.refresh(contract)

    return ContractRead.model_validate(contract)


@router.delete("/{contract_id}", status_code=204)
async def delete_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a draft contract."""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if contract.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft contracts can be deleted",
        )

    await db.delete(contract)
    await db.commit()


@router.post("/{contract_id}/send", response_model=ContractRead)
async def send_contract(
    contract_id: str,
    data: ContractSend,
    db: AsyncSession = Depends(get_db),
) -> ContractRead:
    """Send contract for signing."""
    service = ContractService(db)

    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.contact))
        .where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if contract.status not in ["draft"]:
        raise HTTPException(
            status_code=400,
            detail="Contract has already been sent",
        )

    # Calculate expiration
    expiry_days = data.expiry_days or 7
    if contract.template:
        expiry_days = data.expiry_days or contract.template.default_expiry_days

    contract.status = "sent"
    contract.sent_at = datetime.now()
    contract.expires_at = service.calculate_expiry_date(expiry_days)

    # Log send action
    await service.log_action(
        contract_id=contract.id,
        action="sent",
        details={
            "expiry_days": expiry_days,
            "send_email": data.send_email,
        },
    )

    # Send email notification
    if data.send_email and contract.contact and contract.contact.email:
        # Generate signing link
        signing_link = f"/sign/{contract.view_token}"

        await email_service.send_contract_notification(
            to_email=contract.contact.email,
            contact_name=contract.contact.full_name,
            contract_title=contract.title,
            signing_link=signing_link,
            expires_at=contract.expires_at,
            custom_message=data.email_message,
        )

    await db.commit()
    await db.refresh(contract)

    return ContractRead.model_validate(contract)


@router.post("/{contract_id}/duplicate", response_model=ContractRead, status_code=201)
async def duplicate_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
) -> ContractRead:
    """Duplicate a contract as a new draft."""
    service = ContractService(db)

    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Generate new contract number
    contract_number = await service.generate_contract_number()

    new_contract = Contract(
        contract_number=contract_number,
        template_id=contract.template_id,
        contact_id=contract.contact_id,
        organization_id=contract.organization_id,
        title=f"{contract.title} (Copy)",
        content=contract.content,
        notes=contract.notes,
        linked_invoice_id=None,  # Don't copy invoice link
        status="draft",
    )

    db.add(new_contract)
    await db.flush()

    # Log creation
    await service.log_action(
        contract_id=new_contract.id,
        action="created",
        details={"duplicated_from": contract_id},
    )

    await db.commit()
    await db.refresh(new_contract)

    return ContractRead.model_validate(new_contract)


@router.post("/{contract_id}/void", response_model=ContractRead)
async def void_contract(
    contract_id: str,
    data: ContractVoid,
    db: AsyncSession = Depends(get_db),
) -> ContractRead:
    """Void/cancel a contract."""
    service = ContractService(db)

    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if contract.status in ["signed", "void"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot void a {contract.status} contract",
        )

    contract.status = "void"

    # Log void action
    await service.log_action(
        contract_id=contract.id,
        action="voided",
        details={"reason": data.reason},
    )

    await db.commit()
    await db.refresh(contract)

    return ContractRead.model_validate(contract)


@router.get("/{contract_id}/audit-log", response_model=list[SignatureAuditLogRead])
async def get_audit_log(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[SignatureAuditLogRead]:
    """Get audit log for a contract."""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    result = await db.execute(
        select(SignatureAuditLog)
        .where(SignatureAuditLog.contract_id == contract_id)
        .order_by(SignatureAuditLog.created_at.desc())
    )
    logs = result.scalars().all()

    return [SignatureAuditLogRead.model_validate(log) for log in logs]


@router.post("/{contract_id}/resend", response_model=ContractRead)
async def resend_contract(
    contract_id: str,
    data: ContractSend,
    db: AsyncSession = Depends(get_db),
) -> ContractRead:
    """Resend contract notification email."""
    service = ContractService(db)

    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.contact))
        .where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if contract.status not in ["sent", "viewed"]:
        raise HTTPException(
            status_code=400,
            detail="Contract must be in sent or viewed status to resend",
        )

    # Update expiration if specified
    if data.expiry_days:
        contract.expires_at = service.calculate_expiry_date(data.expiry_days)

    # Log resend action
    await service.log_action(
        contract_id=contract.id,
        action="resent",
        details={"expiry_days": data.expiry_days},
    )

    # Send email notification
    if data.send_email and contract.contact and contract.contact.email:
        signing_link = f"/sign/{contract.view_token}"

        await email_service.send_contract_notification(
            to_email=contract.contact.email,
            contact_name=contract.contact.full_name,
            contract_title=contract.title,
            signing_link=signing_link,
            expires_at=contract.expires_at,
            custom_message=data.email_message,
        )

    await db.commit()
    await db.refresh(contract)

    return ContractRead.model_validate(contract)


@router.get("/{contract_id}/pdf")
async def download_contract_pdf(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download contract as PDF."""
    if not pdf_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="PDF generation is not available. Please install weasyprint.",
        )

    result = await db.execute(
        select(Contract)
        .options(
            selectinload(Contract.contact),
            selectinload(Contract.organization),
        )
        .where(Contract.id == contract_id)
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
