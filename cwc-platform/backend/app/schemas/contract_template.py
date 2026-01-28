from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict

TemplateCategory = Literal["coaching", "workshop", "consulting", "speaking", "general"]


class ContractTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    content: str  # HTML with merge fields like {{client_name}}
    category: TemplateCategory = "coaching"
    default_expiry_days: int = 7


class ContractTemplateCreate(ContractTemplateBase):
    pass


class ContractTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[TemplateCategory] = None
    default_expiry_days: Optional[int] = None
    is_active: Optional[bool] = None


class ContractTemplateRead(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    content: str
    category: str
    merge_fields: list[str]
    default_expiry_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContractTemplateList(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    category: str
    merge_fields: list[str]
    is_active: bool
    contracts_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContractTemplatePreview(BaseModel):
    """Preview template with sample data merged"""
    name: str
    content: str  # Rendered HTML with sample data
    merge_fields: list[str]


# Merge field helpers
class MergeFieldInfo(BaseModel):
    name: str
    description: str
    category: str  # "auto" or "custom"
    sample_value: str


class MergeFieldsResponse(BaseModel):
    auto_fields: list[MergeFieldInfo]
    custom_fields: list[MergeFieldInfo]
