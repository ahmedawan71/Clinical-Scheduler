from typing import Any
from app.database import supabase

def check_availability(doctor_name: str, date: str):
    response = supabase.table("appointments") \
        .select("appointment_time") \
        .eq("doctor_name", doctor_name) \
        .eq("appointment_date", date) \
        .execute()

    booked_times: list[str] = []
    data: Any = response.data
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                appointment_time = item.get("appointment_time")
                if isinstance(appointment_time, str):
                    booked_times.append(appointment_time)

    all_slots = ["09:00", "10:00", "11:30", "14:00", "15:30"]

    available_slots = [
        slot for slot in all_slots if slot not in booked_times
    ]

    return {
        "doctor": doctor_name,
        "date": date,
        "available_slots": available_slots
    }
