from app.database import supabase
from datetime import datetime, timedelta
from app.utils.logger import agent_logger

def get_patient_appointments(patient_name: str = None, doctor_name: str = None,
                             date_from: str = None, date_to: str = None,
                             include_cancelled: bool = False):
    """Get appointments with flexible filters"""
    
    if not patient_name and not doctor_name:
        return {"success": False, "error": "Provide patient_name or doctor_name"}
    
    query = supabase.table("appointments").select("*")
    
    if not include_cancelled:
        query = query.neq("status", "cancelled")
    
    if patient_name:
        query = query.eq("patient_name", patient_name)
    if doctor_name:
        query = query.eq("doctor_name", doctor_name)
    if date_from:
        query = query.gte("appointment_date", date_from)
    if date_to:
        query = query.lte("appointment_date", date_to)
    
    response = query.order("appointment_date", desc=False).execute()
    
    appointments = response.data or []
    today = datetime.now().strftime("%Y-%m-%d")
    
    upcoming = [a for a in appointments if a["appointment_date"] >= today and a["status"] != "cancelled"]
    past = [a for a in appointments if a["appointment_date"] < today]
    
    return {
        "success": True,
        "upcoming": upcoming,
        "upcoming_count": len(upcoming),
        "past": past[-10:],  # Last 10 past appointments
        "past_count": len(past),
        "total": len(appointments)
    }

def get_appointment_history(patient_name: str):
    """Get full appointment history with statistics"""
    
    if not patient_name:
        return {"success": False, "error": "Patient name required"}
    
    response = supabase.table("appointments").select("*").eq(
        "patient_name", patient_name
    ).order("appointment_date", desc=True).execute()
    
    appointments = response.data or []
    
    if not appointments:
        return {
            "success": True,
            "patient": patient_name,
            "message": "No appointment history found",
            "total_appointments": 0
        }
    
    # Calculate statistics
    stats = {
        "completed": len([a for a in appointments if a.get("status") == "completed"]),
        "cancelled": len([a for a in appointments if a.get("status") == "cancelled"]),
        "no_show": len([a for a in appointments if a.get("status") == "no_show"]),
        "confirmed": len([a for a in appointments if a.get("status") == "confirmed"])
    }
    
    # Frequently visited doctors
    doctor_visits = {}
    for apt in appointments:
        if apt.get("status") != "cancelled":
            doc = apt["doctor_name"]
            doctor_visits[doc] = doctor_visits.get(doc, 0) + 1
    
    frequent_doctors = sorted(doctor_visits.items(), key=lambda x: -x[1])[:3]
    
    # Common appointment types
    type_counts = {}
    for apt in appointments:
        apt_type = apt.get("appointment_type", "consultation")
        type_counts[apt_type] = type_counts.get(apt_type, 0) + 1
    
    return {
        "success": True,
        "patient": patient_name,
        "total_appointments": len(appointments),
        "statistics": stats,
        "frequent_doctors": [{"name": d[0], "visits": d[1]} for d in frequent_doctors],
        "common_appointment_types": type_counts,
        "recent_appointments": appointments[:5],
        "first_visit": appointments[-1]["appointment_date"] if appointments else None
    }