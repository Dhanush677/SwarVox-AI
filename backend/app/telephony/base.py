from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class CallRequest:
    business_id: UUID
    call_id: UUID
    to_number: str
    from_number: str
    intro_message: str
    correlation_id: str


@dataclass(frozen=True)
class CallResult:
    provider: str
    provider_call_id: str
    status: str
    transcript: str
    summary: str
    duration_seconds: int
    outcome: str


class TelephonyProvider(Protocol):
    name: str

    def make_call(self, request: CallRequest) -> CallResult:
        ...

    def hangup_call(self, provider_call_id: str) -> None:
        ...

    def transfer_call(self, provider_call_id: str, target_number: str, summary: str) -> None:
        ...
