from datetime import datetime, timedelta
from app.database import supabase
from app.utils.logger import agent_logger

def check_availability(doctor_name: str, date: str):
    
    if not doctor_name or not date:
        return {"success": False, "error": "Doctor name and date are required"}
    
    response = supabase.table("appointments").select(
        "appointment_time, end_time, patient_name, appointment_type, duration_minutes").eq(
            "doctor_name", doctor_name).eq("appointment_date", date).neq("status", "cancelled").execute()
    
    booked_slots = response.data if response.data else []
    
    # Generate all possible time slots for the day (example: 9am to 5pm with 30 min intervals)
    all_slots = []
    for hour in range(9, 17):
        for minute in [0, 30]:
            all_slots.append(f"{hour:02d}:{minute:02d}")
    
    #determine available slots    
    booked_times = set()
    for slot in booked_slots:
        start = datetime.strptime(slot["appointment_time"], "%H:%M")
        end = datetime.strptime(slot.get("end_time", slot["appointment_time"]), "%H:%M")
    
        #mark all 30 min blocks within the appointment as booked
        current = start
        while current < end:
            booked_times.add(current.strftime("%H:%M"))
            current += timedelta(minutes=30)
            
    available = [
        slot for slot in all_slots if slot not in booked_times
    ]

    return {
        "success": True,
        "doctor": doctor_name,
        "date": date,
        "available_slots": available,
        "booked_count": len(booked_slots),
        "available_count": len(available),
        "utilization": f"{len(booked_slots)}/{len(all_slots)} time blocks used"
    }

def find_next_available(doctor_name:str, preferred_date: str, days_to_search: int = 14):
    
    if not doctor_name or not preferred_date:
        return {"success": False, "error": "Doctor name and preferred date are required"}
    
    try:
        base_date = datetime.strptime(preferred_date, "%Y-%m-%d")
    except ValueError:
        return {"success": False, "error": "Preferred date must be in YYYY-MM-DD format"}
    
    for i in range(days_to_search):
        check_date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        if(base_date + timedelta(days=i)).weekday() >= 5:  # Skip weekends
            continue
        
        availability = check_availability(doctor_name, check_date)
        if availability.get("success") and availability.get("available_slots"):
            return {
                "success": True,
                "doctor": doctor_name,
                "next_available_date": check_date,
                "available_slots": availability["available_slots"],
                "days_from_preferred": i,
                "is_preferred_date": i == 0
            }
    
    return {
        "success": False,
        "error": f"No available slots found for Dr. {doctor_name} within {days_to_search} days",
        "suggestion": "Try a different doctor or increase the search range"
    }        
    
def suggest_alternative_doctors(specialty: str, date: str, preferred_time: str = None):
    """Suggest other doctors when preferred one is unavailable"""
    
    if not specialty or not date:
        return {"success": False, "error": "Specialty and date required"}
    
    # Get doctors with matching specialty
    doctors_response = supabase.table("doctors").select("*").eq(
        "specialty", specialty
    ).eq("active", True).execute()
    
    if not doctors_response.data:
        return {
            "success": False,
            "error": f"No doctors found with specialty: {specialty}"
        }
    
    available_doctors = []
    
    for doctor in doctors_response.data:
        availability = check_availability(doctor["name"], date)
        
        if availability.get("success") and availability.get("available_slots"):
            slots = availability["available_slots"]
            
            # Prioritize if preferred time is available
            has_preferred = preferred_time in slots if preferred_time else False
            
            available_doctors.append({
                "name": doctor["name"],
                "specialty": specialty,
                "available_slots": slots[:5],
                "has_preferred_time": has_preferred,
                "total_available": len(slots)
            })
    
    # Sort by availability (most slots first)
    available_doctors.sort(key=lambda x: (-x["has_preferred_time"], -x["total_available"]))
    
    return {
        "success": True,
        "specialty": specialty,
        "date": date,
        "available_doctors": available_doctors,
        "total_found": len(available_doctors)
    }