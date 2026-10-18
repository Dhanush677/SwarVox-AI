from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.models import CallDirection, CallStatus


class CallRead(BaseModel):
    id: UUID
    business_id: UUID
    customer_id: UUID | None
    event_id: UUID | None
    agent_id: UUID | None
    direction: CallDirection
    status: CallStatus
    provider: str
    provider_call_id: str | None
    from_number: str | None
    to_number: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int
    transcript: str | None
    summary: str | None
    intent: str | None
    outcome: str | None
    escalation_status: str
    failure_reason: str | None
    usage_metrics: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
