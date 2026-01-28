from datetime import datetime
from pydantic import BaseModel
from typing import Literal


InteractionType = Literal["email", "call", "meeting", "note"]
Direction = Literal["inbound", "outbound"]


class InteractionBase(BaseModel):
    interaction_type: InteractionType
    subject: str | None = None
    content: str | None = None
    direction: Direction | None = None


class InteractionCreate(InteractionBase):
    contact_id: str


class InteractionResponse(InteractionBase):
    id: str
    contact_id: str
    gmail_message_id: str | None = None
    created_at: datetime
    created_by: str | None = None

    class Config:
        from_attributes = True


class InteractionList(BaseModel):
    items: list[InteractionResponse]
    total: int
