from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Business
from app.services.bootstrap import ensure_demo_business


def get_current_business(db: Session = Depends(get_db)) -> Business:
    # Phase 1 uses a bootstrapped demo tenant. Authenticated tenant resolution arrives in Phase 4.
    return ensure_demo_business(db)