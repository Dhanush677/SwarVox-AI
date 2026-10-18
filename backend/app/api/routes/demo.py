from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.events import EventEngine
from app.models import Business
from app.schemas.demo import LeadFormCreate
from app.schemas.events import CustomerPayload, EventCreate, EventIngestResponse, EventRead

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/lead", response_model=EventIngestResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_demo_lead(
    payload: LeadFormCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> EventIngestResponse:
    event_payload = EventCreate(
        event_type="lead.created",
        customer=CustomerPayload(name=payload.name, phone=payload.phone, email=payload.email),
        payload={
            "service": payload.service,
            "preferred_date": payload.preferred_date,
            "preferred_time": payload.preferred_time,
        },
        source="demo_form",
        external_event_id=f"demo:{payload.phone}:{payload.preferred_date}:{payload.preferred_time}",
    )
    result = EventEngine(db).ingest(business, event_payload)
    return EventIngestResponse(
        event=EventRead.model_validate(result.event),
        duplicate=result.duplicate,
        call_id=result.call_id,
        message=result.message,
    )
