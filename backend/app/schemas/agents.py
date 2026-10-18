from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AgentRead(BaseModel):
    id: UUID
    name: str
    language: str
    voice: str | None
    personality: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
