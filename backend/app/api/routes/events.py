from datetime import datetime, time, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.events import EventEngine
from app.models import Business, Event
from app.schemas.events import EventCreate, EventIngestResponse, EventRead

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_event(
    payload: EventCreate,
    request: Request,
    x_swarvox_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> EventIngestResponse:
    raw_body = await request.body()
    engine = EventEngine(db)

    if not engine.verify_signature(raw_body, x_swarvox_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    result = engine.ingest(business, payload)

    return EventIngestResponse(
        event=EventRead.model_validate(result.event),
        duplicate=result.duplicate,
        call_id=result.call_id,
        message=result.message,
    )


@router.get("/leads/today/count")
def leads_today_count(
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    start_of_day = datetime.combine(
        now.date(),
        time.min,
        tzinfo=timezone.utc,
    )
    end_of_day = datetime.combine(
        now.date(),
        time.max,
        tzinfo=timezone.utc,
    )

    count = db.scalar(
        select(func.count())
        .select_from(Event)
        .where(
            Event.business_id == business.id,
            Event.event_type == "lead.created",
            Event.created_at >= start_of_day,
            Event.created_at <= end_of_day,
        )
    )

    return {"count": count or 0}
@router.get("/appointments/today/count")
def appointments_today_count(
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    start_of_day = datetime.combine(
        now.date(),
        time.min,
        tzinfo=timezone.utc,
    )
    end_of_day = datetime.combine(
        now.date(),
        time.max,
        tzinfo=timezone.utc,
    )

    count = db.scalar(
        select(func.count())
        .select_from(Event)
        .where(
            Event.business_id == business.id,
            Event.event_type == "appointment.created",
            Event.created_at >= start_of_day,
            Event.created_at <= end_of_day,
        )
    )

    return {"count": count or 0}



@router.get("", response_model=list[EventRead])
def list_events(
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> list[Event]:
    return list(
        db.scalars(
            select(Event)
            .where(Event.business_id == business.id)
            .order_by(Event.created_at.desc())
            .limit(100)
        )
    )


@router.get("/{event_id}", response_model=EventRead)
def get_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> Event:
    event = db.get(Event, event_id)

    if not event or event.business_id != business.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event