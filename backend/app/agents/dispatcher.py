from app.agents.scheduling_agent import (
    check_availability, find_next_available, 
    suggest_alternative_doctors, get_optimal_slots
)
from app.agents.booking_agent import book_appointment, get_appointment_types
from app.agents.reschedule_agent import reschedule_appointment
from app.agents.cancellation_agent import cancel_appointment, confirm_late_cancellation
from app.agents.patient_agent import get_patient_appointments, get_appointment_history
from app.utils.logger import agent_logger

def execute(intent: str, parameters: dict):
    """Central dispatcher with all Phase 3 handlers"""
    
    if not intent or not isinstance(parameters, dict):
        return {"success": False, "error": "Invalid request format"}
    
    handlers = {
        # Phase 1-2 handlers
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
            p.get("patient_name"), p.get("doctor_name"),
            p.get("date_from"), p.get("date_to"), p.get("include_cancelled", False)
        ),
        "get_history": lambda p: get_appointment_history(p.get("patient_name")),
        "get_appointment_types": lambda p: get_appointment_types(),
        
        # Phase 3 - Smart scheduling handlers
        "find_next_available": lambda p: find_next_available(
            p.get("doctor_name"), p.get("preferred_date"), p.get("days_to_search", 14)
        ),
        "suggest_alternatives": lambda p: suggest_alternative_doctors(
            p.get("specialty"), p.get("date"), p.get("time")
        ),
        "get_optimal_slots": lambda p: get_optimal_slots(
            p.get("doctor_name"), p.get("date"), p.get("duration_minutes", 30)
        ),
        
        # General inquiry handler
        "general_inquiry": lambda p: {
            "success": True,
            "message": "I can help you with booking, rescheduling, or cancelling appointments. What would you like to do?"
        }
    }
    
    handler = handlers.get(intent)
    if not handler:
        agent_logger.warning(f"Unknown intent: {intent}")
        return {"success": False, "error": f"Unknown intent: {intent}"}
    
    try:
        agent_logger.info(f"Executing: {intent}")
        return handler(parameters)
    except Exception as e:
        agent_logger.error(f"Failed {intent}: {str(e)}")
        return {"success": False, "error": str(e)}