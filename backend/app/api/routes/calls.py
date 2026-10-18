from datetime import datetime, time, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models import Business, Call
from app.schemas.calls import CallRead

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("/today/count")
def calls_today_count(
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    start_of_day = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    end_of_day = datetime.combine(now.date(), time.max, tzinfo=timezone.utc)

    count = db.scalar(
        select(func.count())
        .select_from(Call)
        .where(
            Call.business_id == business.id,
            Call.created_at >= start_of_day,
            Call.created_at <= end_of_day,
        )
    )

    return {"count": count or 0}


@router.get("", response_model=list[CallRead])
def list_calls(
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> list[Call]:
    return list(
        db.scalars(
            select(Call)
            .where(Call.business_id == business.id)
            .order_by(Call.created_at.desc())
            .limit(100)
        )
    )


@router.get("/{call_id}", response_model=CallRead)
def get_call(
    call_id: UUID,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> Call:
    call = db.get(Call, call_id)

    if not call or call.business_id != business.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found",
        )

    return call