from app.database import supabase

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

    return {
        "status": "confirmed",
        "appointment": response.data
    }
