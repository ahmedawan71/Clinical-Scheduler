from app.database import supabase
from app.utils.email_service import send_email
from app.utils.logger import agent_logger
from datetime import datetime, timedelta
from app.agents.waitlist_agent import check_waitlist_on_cancellation

CANCELLATION_NOTICE_HOURS = 24

def cancel_appointment(appointment_id: str = None, patient_name: str = None, 
                       date: str = None, reason: str = None, force: bool = False):
    """
    Cancel appointment by ID or patient name + date.
    Enforces cancellation policy unless force=True.
    """
    
    # Find the appointment
    if appointment_id:
        query = supabase.table("appointments").select("*").eq("id", appointment_id)
    elif patient_name and date:
        query = supabase.table("appointments").select("*").eq(
            "patient_name", patient_name
        ).eq("appointment_date", date).eq("status", "confirmed")
    else:
        return {"success": False, "error": "Provide appointment_id OR (patient_name + date)"}
    
    response = query.execute()
    
    if not response.data:
        return {"success": False, "error": "Appointment not found or already cancelled"}
    
    # Handle multiple appointments found
    if len(response.data) > 1 and not appointment_id:
        return {
            "success": False,
            "error": "Multiple appointments found. Please specify which one to cancel.",
            "appointments": [
                {"id": a["id"], "time": a["appointment_time"], "doctor": a["doctor_name"]}
                for a in response.data
            ]
        }
    
    appointment = response.data[0]
    
    # Check cancellation policy
    apt_datetime = datetime.strptime(
        f"{appointment['appointment_date']} {appointment['appointment_time']}", 
        "%Y-%m-%d %H:%M"
    )
    hours_until = (apt_datetime - datetime.now()).total_seconds() / 3600
    
    if hours_until < CANCELLATION_NOTICE_HOURS and not force:
        return {
            "success": False,
            "warning": f"Less than {CANCELLATION_NOTICE_HOURS} hours notice. Cancellation fee may apply.",
            "hours_until_appointment": round(hours_until, 1),
            "confirm_required": True,
            "appointment": {
                "id": appointment["id"],
                "date": appointment["appointment_date"],
                "time": appointment["appointment_time"],
                "doctor": appointment["doctor_name"]
            }
        }
    
    # Perform cancellation
    try:
        update_response = supabase.table("appointments").update({
            "status": "cancelled",
            "cancellation_reason": reason,
            "cancelled_at": datetime.utcnow().isoformat()
        }).eq("id", appointment["id"]).execute()
        
        if update_response.data:
            agent_logger.info(f"Appointment cancelled: {appointment['id']}")
            
            #check waitlist for the freed slot
            waitlist_result = check_waitlist_on_cancellation(
                appointment["doctor_name"],
                appointment["appointment_date"],
                appointment["appointment_time"]
            )
            
            
            # Send notification
            if appointment.get("patient_email"):
                send_email(
                    to_email=appointment["patient_email"],
                    subject="Appointment Cancelled",
                    body=f"""Your appointment with {appointment['doctor_name']} on {appointment['appointment_date']} at {appointment['appointment_time']} has been cancelled.

Reason: {reason or 'Not specified'}

If you would like to reschedule, please contact us or use our booking system."""
                )
            
            return {
                "success": True,
                "message": f"Appointment cancelled successfully",
                "cancelled_appointment": {
                    "id": appointment["id"],
                    "date": appointment["appointment_date"],
                    "time": appointment["appointment_time"],
                    "doctor": appointment["doctor_name"]
                },
                "slot_freed": True,
                "waitlist_notified" : waitlist_result.get("patients_notified", [])
            }
            
    except Exception as e:
        agent_logger.error(f"Cancellation failed: {str(e)}")
        return {"success": False, "error": f"Cancellation failed: {str(e)}"}
    
    return {"success": False, "error": "Cancellation failed unexpectedly"}

def confirm_late_cancellation(appointment_id: str, reason: str = None):
    """Confirm cancellation when within policy window"""
    return cancel_appointment(appointment_id=appointment_id, reason=reason, force=True)