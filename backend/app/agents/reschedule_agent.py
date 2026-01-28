from app.database import supabase

def reschedule_appointment(parameters: dict):
    response = supabase.table("appointments") \
        .update({
            "appointment_date": parameters.get("new_date"),
            "appointment_time": parameters.get("new_time")
        }) \
        .eq("id", parameters.get("appointment_id")) \
        .execute()

    return {
        "status": "rescheduled",
        "updated": response.data
    }
