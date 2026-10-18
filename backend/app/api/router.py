from fastapi import APIRouter

from app.api.routes.agents import router as agents_router
from app.api.routes.calls import router as calls_router
from app.api.routes.events import router as events_router
from app.api.routes.workflows import router as workflows_router

api_router = APIRouter()

api_router.include_router(agents_router)
api_router.include_router(events_router)
api_router.include_router(calls_router)
api_router.include_router(workflows_router)