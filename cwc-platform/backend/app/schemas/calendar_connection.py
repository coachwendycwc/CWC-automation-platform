from datetime import datetime

from pydantic import BaseModel


class CalendarConnectionResponse(BaseModel):
    id: str
    provider: str
    account_email: str | None = None
    account_name: str | None = None
    external_account_id: str | None = None
    calendar_id: str
    calendar_name: str | None = None
    sync_direction: str
    conflict_check_enabled: bool
    is_primary: bool
    is_active: bool
    provider_metadata: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
