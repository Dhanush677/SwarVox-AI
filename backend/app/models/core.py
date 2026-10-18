import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def uuid_pk() -> uuid.UUID:
    return uuid.uuid4()


JSONType = JSON().with_variant(JSONB, "postgresql")


class EventStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    CALLING = "CALLING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


class CallStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    INITIATED = "INITIATED"
    RINGING = "RINGING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NO_ANSWER = "NO_ANSWER"
    BUSY = "BUSY"
    CANCELLED = "CANCELLED"


class CallDirection(str, enum.Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Business(Base, TimestampMixin):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)

    agents: Mapped[list["Agent"]] = relationship(back_populates="business")
    customers: Mapped[list["Customer"]] = relationship(back_populates="business")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="owner", nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(64), default="en-IN", nullable=False)
    voice: Mapped[str | None] = mapped_column(String(128), nullable=True)
    personality: Mapped[str] = mapped_column(String(255), default="professional, warm, concise", nullable=False)
    system_instructions: Mapped[str] = mapped_column(Text, nullable=False)
    allowed_tools: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    escalation_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business: Mapped[Business] = relationship(back_populates="agents")


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("business_id", "phone", name="uq_customer_business_phone"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferences: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)

    business: Mapped[Business] = relationship(back_populates="customers")


class Workflow(Base, TimestampMixin):
    __tablename__ = "workflows"
    __table_args__ = (
        Index("ix_workflows_business_trigger_enabled", "business_id", "trigger", "enabled"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    trigger: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agents.id"), nullable=True)
    timing: Mapped[str] = mapped_column(String(64), default="immediate", nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Event(Base, TimestampMixin):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("business_id", "idempotency_key", name="uq_event_business_idempotency"),
        Index("ix_events_business_status_created", "business_id", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(128), default="api", nullable=False)
    external_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_payload: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.RECEIVED, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("workflows.id"), nullable=True)
    validation_errors: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)


class Call(Base, TimestampMixin):
    __tablename__ = "calls"
    __table_args__ = (Index("ix_calls_business_status_created", "business_id", "status", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"), index=True, nullable=False)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("events.id"), nullable=True)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agents.id"), nullable=True)
    direction: Mapped[CallDirection] = mapped_column(Enum(CallDirection), nullable=False)
    status: Mapped[CallStatus] = mapped_column(Enum(CallStatus), default=CallStatus.QUEUED, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_call_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    from_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_number: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    escalation_status: Mapped[str] = mapped_column(String(64), default="none", nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_metrics: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)


class CallEvent(Base, TimestampMixin):
    __tablename__ = "call_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    call_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("calls.id"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"), index=True, nullable=False)
    actor_type: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audit_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONType, default=dict, nullable=False)


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"), index=True, nullable=False)
    plan_name: Mapped[str] = mapped_column(String(128), default="starter", nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="trialing", nullable=False)
    usage_limits: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
