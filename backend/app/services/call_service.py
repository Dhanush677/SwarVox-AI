from sqlalchemy.orm import Session

from app.agents import build_intro_message
from app.core.config import get_settings
from app.models import Business, Call, CallDirection, CallEvent, CallStatus, Customer, Event, Workflow
from app.telephony import CallRequest, MockTelephonyProvider, TelephonyProvider


class CallService:
    def __init__(self, db: Session, provider: TelephonyProvider | None = None):
        self.db = db
        self.settings = get_settings()
        self.provider = provider or MockTelephonyProvider()

    def start_outbound_call(self, event: Event, workflow: Workflow, customer: Customer, business: Business) -> Call:
        call = Call(
            business_id=event.business_id,
            customer_id=customer.id,
            event_id=event.id,
            agent_id=workflow.agent_id,
            direction=CallDirection.OUTBOUND,
            status=CallStatus.INITIATED,
            provider=self.provider.name,
            from_number=self.settings.default_caller_id,
            to_number=customer.phone,
            intent=workflow.config.get("objective"),
            usage_metrics={
                "telephony_seconds": 0,
                "llm_tokens": 0,
                "stt_seconds": 0,
                "tts_characters": 0,
                "estimated_cost": 0,
            },
        )
        self.db.add(call)
        self.db.flush()

        intro_message = build_intro_message(event, business.name)
        result = self.provider.make_call(
            CallRequest(
                business_id=event.business_id,
                call_id=call.id,
                to_number=customer.phone,
                from_number=self.settings.default_caller_id,
                intro_message=intro_message,
                correlation_id=event.correlation_id,
            )
        )

        call.provider_call_id = result.provider_call_id
        call.status = CallStatus(result.status)
        call.transcript = result.transcript
        call.summary = result.summary
        call.duration_seconds = result.duration_seconds
        call.outcome = result.outcome
        call.usage_metrics = {
            **call.usage_metrics,
            "telephony_seconds": result.duration_seconds,
            "estimated_cost": 0,
        }
        self.db.add(
            CallEvent(
                call_id=call.id,
                event_type="mock.call.completed",
                payload={
                    "provider_call_id": result.provider_call_id,
                    "correlation_id": event.correlation_id,
                    "outcome": result.outcome,
                },
            )
        )
        self.db.flush()
        return call
