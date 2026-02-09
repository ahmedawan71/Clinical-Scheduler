from app.agents.scheduling_agent import check_availability
from app.agents.booking_agent import book_appointment
from app.agents.reschedule_agent import reschedule_appointment
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
