from pydantic import BaseModel, Field


class LeadFormCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=7, max_length=32)
    email: str | None = Field(default=None, max_length=255)
    service: str = Field(min_length=1, max_length=255)
    preferred_date: str = Field(min_length=4, max_length=32)
    preferred_time: str = Field(min_length=2, max_length=32)
