from app.agents.scheduling_agent import check_availability
from app.agents.booking_agent import book_appointment
from app.agents.reschedule_agent import reschedule_appointment
from app.agents.cancellation_agent import cancel_appointment, confirm_late_cancellation
from app.agents.patient_agent import get_patient_appointments, get_appointment_history
#from app.agents.notification_agent import send_notification
import logging

logger = logging.getLogger(__name__)

def execute(intent: str, parameters: dict):
    
    if not intent or not isinstance(parameters, dict):
        return {"success": False, "error": "Invalid request format"}
    
    handlers = {
        "check_availability": lambda p: check_availability(
            p.get("doctor_name"), p.get("date")
        ),
        "book_appointment": lambda p: book_appointment(
            p.get("patient_name"), p.get("doctor_name"), p.get("date"), 
            p.get("time"), p.get("appointment_type", "consultation"),
            p.get("patient_email"), p.get("patient_phone"), p.get("notes")
        ),
        "reschedule_appointment": lambda p: reschedule_appointment(
            p.get("appointment_id"), p.get("new_date"), p.get("new_time")
        ),
        "cancel_appointment": lambda p: cancel_appointment(
            p.get("appointment_id"), p.get("patient_name"),
            p.get("date"), p.get("reason"), p.get("force", False)
        ),
        "confirm_cancellation": lambda p: confirm_late_cancellation(
            p.get("appointment_id"), p.get("reason")
        ),
        "get_appointments": lambda p: get_patient_appointments(
            p.get("patient_name"), p.get("doctor_name"), p.get("date_from"), p.get("date_to"), p.get("include_cancelled", False)
        ),
        "get_history": lambda p: get_appointment_history(p.get("patient_name")),
        "get_appointment_types": lambda p: get_appointment_history(),
        #"send_notification": send_notification
    }
    
    handler = handlers.get(intent)
    
    if not handler:
        logger.warning(f"Unknown intent received: {intent}")
        return {"success": False, "error": f"Unknown intent: {intent}"}
    
    try:
        logger.info(f"Executing intent: {intent} with parameters: {parameters}")
        result = handler(parameters)
        return result
    except Exception as e:
        logger.error(f"Error failed for {intent}: {str(e)}")
        return {"success": False, "error": f"Execution failed: {str(e)}"}
    return {"error": "Unknown intent"}
