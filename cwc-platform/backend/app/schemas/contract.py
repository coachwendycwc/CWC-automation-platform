from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict

ContractStatus = Literal["draft", "sent", "viewed", "signed", "expired", "declined", "void"]
SignatureType = Literal["drawn", "typed"]


# Signature audit log schemas
class SignatureAuditLogRead(BaseModel):
    id: str
    contract_id: str
    action: str
    actor_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Contract schemas
class ContractBase(BaseModel):
    contact_id: str
    organization_id: Optional[str] = None
    title: str
    notes: Optional[str] = None


class ContractCreate(ContractBase):
    template_id: Optional[str] = None
    content: Optional[str] = None  # If not using template
    merge_data: Optional[dict] = None  # Data to merge into template
    linked_invoice_id: Optional[str] = None
    expiry_days: Optional[int] = None  # Override template default


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    notes: Optional[str] = None
    linked_invoice_id: Optional[str] = None


class ContractRead(BaseModel):
    id: str
    contract_number: str
    template_id: Optional[str] = None
    contact_id: str
    organization_id: Optional[str] = None
    title: str
    content: str
    status: str
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    decline_reason: Optional[str] = None
    signer_name: Optional[str] = None
    signer_email: Optional[str] = None
    signature_type: Optional[str] = None
    content_hash: Optional[str] = None
    linked_invoice_id: Optional[str] = None
    view_token: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContractList(BaseModel):
    id: str
    contract_number: str
    title: str
    contact_id: str
    contact_name: Optional[str] = None
    organization_name: Optional[str] = None
    status: str
    sent_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContractDetail(ContractRead):
    """Extended contract details with related data"""
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    organization_name: Optional[str] = None
    template_name: Optional[str] = None
    linked_invoice_number: Optional[str] = None
    audit_logs: list[SignatureAuditLogRead] = []


class ContractSend(BaseModel):
    send_email: bool = True
    email_message: Optional[str] = None
    expiry_days: Optional[int] = None  # Override default


class ContractVoid(BaseModel):
    reason: Optional[str] = None


class ContractStats(BaseModel):
    total_contracts: int
    draft_count: int
    sent_count: int
    signed_count: int
    pending_signature_count: int
    declined_count: int
    expired_count: int
    signed_this_month: int


# Public contract view (for signing page)
class ContractPublic(BaseModel):
    contract_number: str
    title: str
    content: str
    status: str
    expires_at: Optional[datetime] = None
    is_expired: bool
    can_sign: bool
    contact_name: str
    organization_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Signature submission
class SignatureSubmit(BaseModel):
    signer_name: str
    signer_email: str
    signature_data: str  # Base64 encoded signature image
    signature_type: SignatureType
    agreed_to_terms: bool = True


class DeclineContract(BaseModel):
    reason: Optional[str] = None
