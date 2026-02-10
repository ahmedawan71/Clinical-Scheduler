from app.database import supabase
from app.utils.email_service import send_email
from app.utils.logger import agent_logger
from datetime import datetime, timedelta
from typing import List

async def send_appointment_reminders(hours_before: int = 24) -> dict:
    """Send reminders for upcoming appointments"""
    
    target_datetime = datetime.now() + timedelta(hours=hours_before)
    target_date = target_datetime.strftime("%Y-%m-%d")
    
    response = supabase.table("appointments").select("*").eq(
        "appointment_date", target_date
    ).eq("status", "confirmed").eq("reminder_sent", False).execute()
    
    appointments = response.data or []
    sent_count = 0
    failed = []
    
    for appointment in appointments:
        if not appointment.get("patient_email"):
            continue
        
        email_body = f"""
Dear {appointment['patient_name']},

This is a friendly reminder about your upcoming appointment:

📅 Date: {appointment['appointment_date']}
🕐 Time: {appointment['appointment_time']}
👨‍⚕️ Doctor: Dr. {appointment['doctor_name']}
📋 Type: {appointment.get('appointment_type', 'Consultation').title()}
⏱️ Duration: {appointment.get('duration_minutes', 30)} minutes

Please arrive 10-15 minutes early to complete any necessary paperwork.

If you need to reschedule or cancel, please contact us at least 24 hours in advance.

Thank you for choosing our clinic!
        """
        
        try:
            success = send_email(
                to_email=appointment["patient_email"],
                subject=f"Reminder: Appointment Tomorrow with Dr. {appointment['doctor_name']}",
                body=email_body
            )
            
            if success:
                supabase.table("appointments").update({
                    "reminder_sent": True
                }).eq("id", appointment["id"]).execute()
                sent_count += 1
                agent_logger.info(f"Reminder sent for appointment {appointment['id']}")
            else:
                failed.append(appointment["id"])
        except Exception as e:
            agent_logger.error(f"Failed to send reminder for {appointment['id']}: {e}")
            failed.append(appointment["id"])
    
    return {
        "success": True,
        "reminders_sent": sent_count,
        "failed": len(failed),
        "target_date": target_date,
        "total_found": len(appointments)
    }

def schedule_follow_up(appointment_id: str, days_after: int = 14, notes: str = None):
    """Suggest follow-up appointment after a visit"""
    
    original = supabase.table("appointments").select("*").eq("id", appointment_id).execute()
    
    if not original.data:
        return {"success": False, "error": "Original appointment not found"}
    
    apt = original.data[0]
    
    try:
        follow_up_date = datetime.strptime(apt["appointment_date"], "%Y-%m-%d") + timedelta(days=days_after)
        
        # Skip weekends
        while follow_up_date.weekday() >= 5:
            follow_up_date += timedelta(days=1)
        
        follow_up_date_str = follow_up_date.strftime("%Y-%m-%d")
    except Exception as e:
        return {"success": False, "error": f"Date calculation failed: {e}"}
    
    return {
        "success": True,
        "suggested_follow_up": {
            "patient_name": apt["patient_name"],
            "doctor_name": apt["doctor_name"],
            "suggested_date": follow_up_date_str,
            "appointment_type": "follow_up",
            "reference_appointment_id": appointment_id,
            "notes": notes or f"Follow-up to appointment on {apt['appointment_date']}"
        },
        "message": f"Follow-up suggested for {follow_up_date_str}"
    }

def get_pending_reminders() -> dict:
    """Get list of appointments pending reminders"""
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    response = supabase.table("appointments").select(
        "id, patient_name, doctor_name, appointment_date, appointment_time, patient_email"
    ).eq("appointment_date", tomorrow).eq("status", "confirmed").eq("reminder_sent", False).execute()
    
    return {
        "success": True,
        "pending_count": len(response.data or []),
        "appointments": response.data or []
    }