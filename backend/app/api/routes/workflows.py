from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.database.session import get_db
from app.models import Business, Workflow
from app.schemas.workflows import WorkflowEnabledUpdate, WorkflowRead

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("", response_model=list[WorkflowRead])
def list_workflows(
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> list[Workflow]:
    return list(
        db.scalars(
            select(Workflow)
            .where(Workflow.business_id == business.id)
            .order_by(Workflow.created_at.asc())
        )
    )


@router.patch("/{workflow_id}/enabled", response_model=WorkflowRead)
def update_workflow_enabled(
    workflow_id: UUID,
    payload: WorkflowEnabledUpdate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
) -> Workflow:
    workflow = db.scalar(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.business_id == business.id,
        )
    )

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    workflow.enabled = payload.enabled
    db.commit()
    db.refresh(workflow)

    return workflow