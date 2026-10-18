from uuid import uuid4

from app.telephony.base import CallRequest, CallResult


class MockTelephonyProvider:
    name = "mock"

    def make_call(self, request: CallRequest) -> CallResult:
        transcript = (
            f"AI: {request.intro_message}\n"
            "Customer: Yes, I am interested. Please confirm the details.\n"
            "AI: Thank you. I have recorded your confirmation and the business team can follow up."
        )
        return CallResult(
            provider=self.name,
            provider_call_id=f"mock_{uuid4().hex}",
            status="COMPLETED",
            transcript=transcript,
            summary="Mock outbound call completed. Customer confirmed interest and requested follow-up.",
            duration_seconds=42,
            outcome="confirmed",
        )

    def hangup_call(self, provider_call_id: str) -> None:
        return None

    def transfer_call(self, provider_call_id: str, target_number: str, summary: str) -> None:
        return None
