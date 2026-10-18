from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models import Agent, Business
from app.schemas.agents import AgentRead

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentRead])
def list_agents(
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> list[Agent]:
    return list(
        db.scalars(
            select(Agent)
            .where(Agent.business_id == business.id)
            .order_by(Agent.created_at.desc())
        )
    )
