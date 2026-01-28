"""
Public contract router for signing flow.
No authentication required - uses view_token for access.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.contract import Contract
from app.schemas.contract import (
    ContractPublic,
    SignatureSubmit,
    DeclineContract,
)
from app.services.contract_service import ContractService
from app.services.email_service import email_service

router = APIRouter(prefix="/api/contract", tags=["public-contract"])


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request."""
    return request.headers.get("User-Agent", "unknown")


@router.get("/{token}", response_model=ContractPublic)
async def view_contract(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ContractPublic:
    """View a contract using its public token."""
    service = ContractService(db)

    result = await db.execute(
        select(Contract)
        .options(
            selectinload(Contract.contact),
            selectinload(Contract.organization),
        )
        .where(Contract.view_token == token)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Check if contract is accessible
    if contract.status == "draft":
        raise HTTPException(status_code=404, detail="Contract not found")

    if contract.status == "void":
        raise HTTPException(
            status_code=410,
            detail="This contract has been cancelled",
        )

    # Check expiration
    is_expired = False
    if contract.expires_at and datetime.now() > contract.expires_at:
        is_expired = True
        if contract.status in ["sent", "viewed"]:
            contract.status = "expired"
            await service.log_action(
                contract_id=contract.id,
                action="expired",
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
            )
            await db.commit()

    # Mark as viewed if first view
    if contract.status == "sent":
        contract.status = "viewed"
        contract.viewed_at = datetime.now()

        await service.log_action(
            contract_id=contract.id,
            action="viewed",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        await db.commit()
        await db.refresh(contract)

    return ContractPublic(
        contract_number=contract.contract_number,
        title=contract.title,
        content=contract.content,
        status=contract.status,
        expires_at=contract.expires_at,
        is_expired=is_expired,
        can_sign=contract.can_be_signed(),
        contact_name=contract.contact.full_name if contract.contact else "Unknown",
        organization_name=contract.organization.name if contract.organization else None,
    )


@router.post("/{token}/sign", response_model=ContractPublic)
async def sign_contract(
    token: str,
    data: SignatureSubmit,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ContractPublic:
    """Submit signature for a contract."""
    service = ContractService(db)

    result = await db.execute(
        select(Contract)
        .options(
            selectinload(Contract.contact),
            selectinload(Contract.organization),
        )
        .where(Contract.view_token == token)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Validate terms acceptance
    if not data.agreed_to_terms:
        raise HTTPException(
            status_code=400,
            detail="You must agree to the terms to sign this contract",
        )

    # Check if can be signed
    if not contract.can_be_signed():
        if contract.status == "signed":
            raise HTTPException(
                status_code=400,
                detail="This contract has already been signed",
            )
        elif contract.status == "expired":
            raise HTTPException(
                status_code=400,
                detail="This contract has expired",
            )
        elif contract.status == "declined":
            raise HTTPException(
                status_code=400,
                detail="This contract has been declined",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="This contract cannot be signed",
            )

    # Get client info
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Mark as signed
    contract.mark_as_signed(
        signer_name=data.signer_name,
        signer_email=data.signer_email,
        signer_ip=client_ip,
        signature_data=data.signature_data,
        signature_type=data.signature_type,
    )

    # Log signature
    await service.log_action(
        contract_id=contract.id,
        action="signed",
        actor_email=data.signer_email,
        ip_address=client_ip,
        user_agent=user_agent,
        details={
            "signer_name": data.signer_name,
            "signature_type": data.signature_type,
            "content_hash": contract.content_hash,
            "signature_hash": contract.signature_hash,
        },
    )

    await db.commit()
    await db.refresh(contract)

    # Send confirmation email to signer
    await email_service.send_contract_signed_confirmation(
        to_email=data.signer_email,
        contact_name=data.signer_name,
        contract_title=contract.title,
        contract_number=contract.contract_number,
        signed_at=contract.signed_at,
    )

    # Send notification email to admin
    await email_service.send_contract_signed_admin_notification(
        contract_title=contract.title,
        contract_number=contract.contract_number,
        signer_name=data.signer_name,
        signer_email=data.signer_email,
        signed_at=contract.signed_at,
    )

    return ContractPublic(
        contract_number=contract.contract_number,
        title=contract.title,
        content=contract.content,
        status=contract.status,
        expires_at=contract.expires_at,
        is_expired=False,
        can_sign=False,
        contact_name=contract.contact.full_name if contract.contact else "Unknown",
        organization_name=contract.organization.name if contract.organization else None,
    )


@router.post("/{token}/decline", response_model=ContractPublic)
async def decline_contract(
    token: str,
    data: DeclineContract,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ContractPublic:
    """Decline a contract."""
    service = ContractService(db)

    result = await db.execute(
        select(Contract)
        .options(
            selectinload(Contract.contact),
            selectinload(Contract.organization),
        )
        .where(Contract.view_token == token)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.can_be_signed():
        raise HTTPException(
            status_code=400,
            detail="This contract cannot be declined",
        )

    # Mark as declined
    contract.status = "declined"
    contract.declined_at = datetime.now()
    contract.decline_reason = data.reason

    # Log decline
    await service.log_action(
        contract_id=contract.id,
        action="declined",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"reason": data.reason},
    )

    await db.commit()
    await db.refresh(contract)

    return ContractPublic(
        contract_number=contract.contract_number,
        title=contract.title,
        content=contract.content,
        status=contract.status,
        expires_at=contract.expires_at,
        is_expired=False,
        can_sign=False,
        contact_name=contract.contact.full_name if contract.contact else "Unknown",
        organization_name=contract.organization.name if contract.organization else None,
    )


@router.get("/{token}/status")
async def get_contract_status(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get basic status of a contract without marking as viewed."""
    result = await db.execute(
        select(Contract).where(Contract.view_token == token)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if contract.status == "draft":
        raise HTTPException(status_code=404, detail="Contract not found")

    is_expired = False
    if contract.expires_at and datetime.now() > contract.expires_at:
        is_expired = True

    return {
        "status": contract.status,
        "is_expired": is_expired,
        "can_sign": contract.can_be_signed() and not is_expired,
        "signed_at": contract.signed_at.isoformat() if contract.signed_at else None,
    }
