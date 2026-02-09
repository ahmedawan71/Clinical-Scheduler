from app.database import supabase
#from app.agents.notification_agent import send_notification
from datetime import datetime, timedelta
from app.utils.logger import agent_logger

APPOINTMENT_DURATIONS = {
    "checkup": 30,
    "consultation": 45,
    "follow_up": 15,
    "procedure": 60,
    "emergency": 30,
    "vaccination": 15,
    "physical_exam": 60,
    "lab_review": 20
}

def book_appointment(patient_name: str, doctor_name: str, date: str, time: str, 
                     appointment_type: str = "consultation", patient_email: str = None,
                     patient_phone: str = None, notes: str = None):
    
    if not all([patient_name, doctor_name, date, time]):
        return {"success": False, "error": "Missing required fields: patient_name, doctor_name, date, time"}
    
    duration = APPOINTMENT_DURATIONS.get(appointment_type.lower(), 30)
    
    if not _check_duration_availability(doctor_name, date, time, duration):
        return {
            "success": False, 
            "error": f"{appointment_type} requires {duration} minutes. Slot conflicts with existing appointment.",
            "suggestion": "Try a different time or check availability first."
        }
    
    end_time = _calculate_end_time(time, duration)
        
    try:
        data = {
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "appointment_date": date,
            "appointment_time": time,
            "end_time": end_time,
            "appointment_type": appointment_type,
            "duration_minutes": duration,
            "patient_email": patient_email,
            "patient_phone": patient_phone,
            "notes": notes,
            "status": "confirmed",
            "created_at": datetime.utcnow().isoformat()
        }

        response = supabase.table("appointments").insert(data).execute()

        if response.data:
            agent_logger.info(f"Appointment booked: {patient_name} with Dr. {doctor_name} on {date}")
            return {
                "success": True,
                "message": f"Appointment booked for {patient_name} with Dr. {doctor_name}",
                "appointment": {
                "id": response.data[0].get("id"),
                "date": date,
                "time": time,
                    "end_time": end_time,
                    "duration": f"{duration} minutes",
                    "type": appointment_type
                }
            }
    except Exception as e:
        agent_logger.error(f"Booking failed: {str(e)}")
        return {"success": False, "error": f"Database error: {str(e)}"}
        
    return {"success": False, "error": "Unknown error occurred during booking"}

def _calculate_end_time(start_time: str, duration: int) -> str:
    start = datetime.strptime(start_time, "%H:%M")
    end = start + timedelta(minutes=duration)
    return end.strftime("%H:%M")

def _check_duration_availability(doctor_name: str, date: str, time: str, duration: int) -> bool:
    response = supabase.table("appointments").select(
        "appointment_time", "end_time"
    ).eq("doctor_name", doctor_name).eq("appointment_date", date).neq("status", "cancelled").execute()

    proposed_start = datetime.strptime(time, "%H:%M")
    proposed_end = proposed_start + timedelta(minutes=duration)
    
    for apt in response.data or []:
        existing_start = datetime.strptime(apt["appointment_time"], "%H:%M")
        existing_end = datetime.strptime(apt.get("end_time") or apt["appointment_time"], "%H:%M")
        
        if not (proposed_end <= existing_start or proposed_start >= existing_end):
            return False
    return True

def get_appointment_types():
    return {
            "types" : [{
                "name": apt_type,
                "duration_minutes": duration
            } for apt_type, duration in APPOINTMENT_DURATIONS.items()]
    }

''' 
    send_notification({
        "email": parameters.get("patient_email"),
        "subject": "Appointment Confirmed",
        "message": f"""
Your appointment has been confirmed.

Doctor: {parameters.get('doctor_name')}
Date: {parameters.get('date')}
Time: {parameters.get('time')}

Thank you.
"""
    })

    return {
        "status": "confirmed",
        "appointment": response.data
    }
'''