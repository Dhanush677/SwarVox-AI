from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import EventStatus


class CustomerPayload(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=7, max_length=32)
    email: str | None = Field(default=None, max_length=255)


class EventCreate(BaseModel):
    event_type: str = Field(min_length=3, max_length=128)
    customer: CustomerPayload
    payload: dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="api", max_length=128)
    external_event_id: str | None = Field(default=None, max_length=255)
    idempotency_key: str | None = Field(default=None, max_length=255)


class EventRead(BaseModel):
    id: UUID
    business_id: UUID
    event_type: str
    source: str
    external_event_id: str | None
    idempotency_key: str
    customer_payload: dict[str, Any]
    payload: dict[str, Any]
    status: EventStatus
    correlation_id: str
    workflow_id: UUID | None
    validation_errors: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventIngestResponse(BaseModel):
    event: EventRead
    duplicate: bool
    call_id: UUID | None = None
    message: str
