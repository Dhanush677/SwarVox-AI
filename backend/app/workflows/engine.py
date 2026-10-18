from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event, Workflow


class WorkflowEngine:
    def __init__(self, db: Session):
        self.db = db

    def find_workflow(self, event: Event) -> Workflow | None:
        return self.db.scalar(
            select(Workflow)
            .where(
                Workflow.business_id == event.business_id,
                Workflow.trigger == event.event_type,
                Workflow.enabled.is_(True),
            )
            .order_by(Workflow.created_at.asc())
        )
