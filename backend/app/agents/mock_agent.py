from app.models import Event


def build_intro_message(event: Event, business_name: str) -> str:
    customer = event.customer_payload
    name = customer.get("name", "there")

    if event.event_type == "appointment.created":
        appointment = event.payload.get("appointment", event.payload)
        service = appointment.get("service", "your appointment")
        date = appointment.get("date") or appointment.get("preferred_date")
        time = appointment.get("time") or appointment.get("preferred_time")
        when = f" on {date} at {time}" if date and time else ""
        return (
            f"Hi {name}, this is SwarVox calling on behalf of {business_name}. "
            f"You requested {service}{when}. I would like to confirm a few details."
        )

    service = event.payload.get("service", "your enquiry")
    return (
        f"Hi {name}, this is SwarVox calling on behalf of {business_name}. "
        f"You recently submitted an enquiry for {service}. I would like to confirm a few details."
    )
