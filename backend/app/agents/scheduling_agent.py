def check_availability(doctor_name: str, date: str):
    return {
        "intent": "check_availability",
        "doctor": doctor_name,
        "date": date,
        "available_slots": ["10:00", "11:30", "14:00"]
    }
