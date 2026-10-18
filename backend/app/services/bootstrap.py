from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Agent, Business, Workflow


DEMO_BUSINESS_NAME = "ABC Dental Clinic"


def ensure_demo_business(db: Session) -> Business:
    business = db.scalar(select(Business).where(Business.name == DEMO_BUSINESS_NAME))
    if business:
        return business

    business = Business(
        name=DEMO_BUSINESS_NAME,
        timezone="Asia/Kolkata",
        phone_number="+910000000000",
        settings={"working_hours": {"start": "09:00", "end": "18:00"}},
    )
    db.add(business)
    db.flush()

    agent = Agent(
        business_id=business.id,
        name="SwarVox Appointment Assistant",
        language="en-IN",
        voice="default",
        personality="warm, clear, professional",
        system_instructions=(
            "You represent ABC Dental Clinic. Confirm appointment or lead details, "
            "answer only from known business information, and escalate when unsure."
        ),
        allowed_tools=["get_customer", "send_confirmation", "transfer_to_human", "end_call"],
        escalation_number="+910000000001",
    )
    db.add(agent)
    db.flush()

    db.add(
        Workflow(
            business_id=business.id,
            name="Immediate lead follow-up",
            trigger="lead.created",
            action="outbound_call",
            agent_id=agent.id,
            timing="immediate",
            config={"objective": "Qualify and confirm the submitted service enquiry."},
            enabled=True,
        )
    )
    db.add(
        Workflow(
            business_id=business.id,
            name="Immediate appointment confirmation",
            trigger="appointment.created",
            action="outbound_call",
            agent_id=agent.id,
            timing="immediate",
            config={"objective": "Confirm appointment details."},
            enabled=True,
        )
    )
    db.commit()
    db.refresh(business)
    return business
