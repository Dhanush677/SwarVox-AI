import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Business, Customer, Event, EventStatus
from app.schemas.events import EventCreate
from app.services.call_service import CallService
from app.workflows import WorkflowEngine


@dataclass(frozen=True)
class EventIngestResult:
    event: Event
    duplicate: bool
    call_id: uuid.UUID | None
    message: str


class EventEngine:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.workflow_engine = WorkflowEngine(db)
        self.call_service = CallService(db)

    def verify_signature(self, raw_body: bytes, signature: str | None) -> bool:
        if self.settings.is_local and not signature:
            return True
        if not signature:
            return False
        digest = hmac.new(self.settings.webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        expected = f"sha256={digest}"
        return hmac.compare_digest(expected, signature)

    def ingest(self, business: Business, payload: EventCreate) -> EventIngestResult:
        idempotency_key = payload.idempotency_key or self._make_idempotency_key(payload)
        existing = self.db.scalar(
            select(Event).where(Event.business_id == business.id, Event.idempotency_key == idempotency_key)
        )
        if existing:
            call_id = self._existing_call_id(existing)
            return EventIngestResult(existing, True, call_id, "Duplicate event ignored; existing result returned.")

        event = Event(
            business_id=business.id,
            event_type=payload.event_type,
            source=payload.source,
            external_event_id=payload.external_event_id,
            idempotency_key=idempotency_key,
            customer_payload=payload.customer.model_dump(),
            payload=payload.payload,
            status=EventStatus.RECEIVED,
            correlation_id=uuid.uuid4().hex,
        )
        self.db.add(event)

        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            existing = self.db.scalar(
                select(Event).where(Event.business_id == business.id, Event.idempotency_key == idempotency_key)
            )
            if existing:
                return EventIngestResult(existing, True, self._existing_call_id(existing), "Duplicate event ignored.")
            raise

        event.status = EventStatus.VALIDATED
        workflow = self.workflow_engine.find_workflow(event)
        if not workflow:
            event.status = EventStatus.COMPLETED
            self.db.commit()
            self.db.refresh(event)
            return EventIngestResult(event, False, None, "Event stored; no enabled workflow matched.")

        event.workflow_id = workflow.id
        event.status = EventStatus.QUEUED
        customer = self._upsert_customer(business, payload)

        if workflow.action == "outbound_call" and workflow.timing == "immediate":
            event.status = EventStatus.CALLING
            call = self.call_service.start_outbound_call(event, workflow, customer, business)
            event.status = EventStatus.COMPLETED
            self.db.commit()
            self.db.refresh(event)
            return EventIngestResult(event, False, call.id, "Event processed and outbound call completed.")

        self.db.commit()
        self.db.refresh(event)
        return EventIngestResult(event, False, None, "Event queued for scheduled processing.")

    def _upsert_customer(self, business: Business, payload: EventCreate) -> Customer:
        customer = self.db.scalar(
            select(Customer).where(Customer.business_id == business.id, Customer.phone == payload.customer.phone)
        )
        if customer:
            customer.name = payload.customer.name
            customer.email = payload.customer.email or customer.email
            return customer

        customer = Customer(
            business_id=business.id,
            name=payload.customer.name,
            phone=payload.customer.phone,
            email=payload.customer.email,
        )
        self.db.add(customer)
        self.db.flush()
        return customer

    def _existing_call_id(self, event: Event) -> uuid.UUID | None:
        from app.models import Call

        call = self.db.scalar(select(Call).where(Call.event_id == event.id).order_by(Call.created_at.desc()))
        return call.id if call else None

    def _make_idempotency_key(self, payload: EventCreate) -> str:
        stable_payload = {
            "event_type": payload.event_type,
            "external_event_id": payload.external_event_id,
            "customer": payload.customer.model_dump(),
            "payload": payload.payload,
        }
        encoded = json.dumps(stable_payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()
