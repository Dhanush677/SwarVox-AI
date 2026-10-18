
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    trigger: str
    action: str
    agent_id: UUID | None
    timing: str
    config: dict[str, Any]
    enabled: bool
    created_at: datetime

class WorkflowEnabledUpdate(BaseModel):
    enabled: bool

class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    trigger: str = Field(min_length=1, max_length=128)
    action: str = Field(min_length=1, max_length=64)
    agent_id: UUID | None = None
    timing: str = Field(default="immediate", max_length=64)
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True