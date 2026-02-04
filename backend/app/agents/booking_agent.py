from app.database import supabase
from app.agents.notification_agent import send_notification

def book_appointment(parameters: dict):
    data = {
        "patient_name": parameters.get("patient_name"),
        "patient_email": parameters.get("patient_email"),
        "doctor_name": parameters.get("doctor_name"),
        "appointment_date": parameters.get("date"),
        "appointment_time": parameters.get("time"),
        "status": "booked"
    }

    response = supabase.table("appointments").insert(data).execute()

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
