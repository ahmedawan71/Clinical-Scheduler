from app.agents.scheduling_agent import check_availability
from app.agents.booking_agent import book_appointment
from app.agents.reschedule_agent import reschedule_appointment
from app.agents.notification_agent import send_notification

def execute(intent: str, parameters: dict):
    if intent == "check_availability":
        return check_availability(
            parameters.get("doctor_name", ""),
            parameters.get("date", "")
        )

    if intent == "book_appointment":
        return book_appointment(parameters)

    if intent == "reschedule_appointment":
        return reschedule_appointment(parameters)

    if intent == "send_notification":
        return send_notification(parameters)

    return {"error": "Unknown intent"}
