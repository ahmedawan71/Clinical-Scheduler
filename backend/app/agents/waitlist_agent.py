from app.database import supabase
from app.utils.email_service import send_email
from app.utils.logger import agent_logger
from datetime import datetime

def add_to_waitlist(patient_name: str, doctor_name: str, preferred_date: str,
                    preferred_time: str = None, patient_email: str = None,
                    appointment_type: str = "consultation"):
    """Add patient to waitlist when no slots available"""
    
    if not all([patient_name, doctor_name, preferred_date]):
        return {"success": False, "error": "Patient name, doctor name, and date required"}
    
    # Check if already on waitlist
    existing = supabase.table("waitlist").select("id").eq(
        "patient_name", patient_name
    ).eq("doctor_name", doctor_name).eq("preferred_date", preferred_date).eq("status", "waiting").execute()
    
    if existing.data:
        return {
            "success": False,
            "error": "Already on waitlist for this doctor and date",
            "waitlist_id": existing.data[0]["id"]
        }
    
    response = supabase.table("waitlist").insert({
        "patient_name": patient_name,
        "doctor_name": doctor_name,
        "preferred_date": preferred_date,
        "preferred_time": preferred_time,
        "patient_email": patient_email,
        "appointment_type": appointment_type,
        "status": "waiting",
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    
    if response.data:
        position = _get_waitlist_position(doctor_name, preferred_date)
        agent_logger.info(f"Added {patient_name} to waitlist for Dr. {doctor_name}")
        
        return {
            "success": True,
            "message": f"Added to waitlist for Dr. {doctor_name} on {preferred_date}",
            "waitlist_id": response.data[0].get("id"),
            "position": position,
            "notification": "You'll be notified if a slot opens up" if patient_email else "Provide email to receive notifications"
        }
    
    return {"success": False, "error": "Failed to add to waitlist"}

def check_waitlist_on_cancellation(doctor_name: str, date: str, time: str):
    """Check waitlist when a slot opens up and notify patients"""
    
    response = supabase.table("waitlist").select("*").eq(
        "doctor_name", doctor_name
    ).eq("preferred_date", date).eq("status", "waiting").order("created_at").execute()
    
    waitlist = response.data or []
    
    if not waitlist:
        return {"success": True, "waitlist_empty": True}
    
    # Find matching patients (preferred time matches or no preference)
    matching = []
    for patient in waitlist:
        if not patient.get("preferred_time") or patient["preferred_time"] == time:
            matching.append(patient)
    
    if not matching:
        matching = waitlist[:3]  # Notify first 3 if no exact match
    
    notified = []
    for patient in matching[:3]:
        if patient.get("patient_email"):
            success = send_email(
                to_email=patient["patient_email"],
                subject=f"Appointment Slot Available with Dr. {doctor_name}",
                body=f""" 
Good news, {patient['patient_name']}!

An appointment slot has opened up:

📅 Date: {date}
🕐 Time: {time}
👨‍⚕️ Doctor: Dr. {doctor_name}

This slot is available on a first-come, first-served basis.
Please book soon to secure this appointment.

If you're no longer interested, you can ignore this message.
                """
            )
            
            if success:
                supabase.table("waitlist").update({
                    "notified_at": datetime.utcnow().isoformat()
                }).eq("id", patient["id"]).execute()
                
                notified.append(patient["patient_name"])
    
    return {
        "success": True,
        "slot_opened": {"date": date, "time": time, "doctor": doctor_name},
        "patients_notified": notified,
        "total_on_waitlist": len(waitlist)
    }

def remove_from_waitlist(waitlist_id: str = None, patient_name: str = None, 
                          doctor_name: str = None, date: str = None):
    """Remove patient from waitlist"""
    
    if waitlist_id:
        query = supabase.table("waitlist").update({
            "status": "removed"
        }).eq("id", waitlist_id)
    elif patient_name and doctor_name and date:
        query = supabase.table("waitlist").update({
            "status": "removed"
        }).eq("patient_name", patient_name).eq("doctor_name", doctor_name).eq("preferred_date", date)
    else:
        return {"success": False, "error": "Provide waitlist_id or patient details"}
    
    response = query.execute()
    
    if response.data:
        return {"success": True, "message": "Removed from waitlist"}
    return {"success": False, "error": "Entry not found"}

def fulfill_waitlist(waitlist_id: str, appointment_id: str):
    """Mark waitlist entry as fulfilled when appointment is booked"""
    
    response = supabase.table("waitlist").update({
        "status": "fulfilled",
        "fulfilled_appointment_id": appointment_id
    }).eq("id", waitlist_id).execute()
    
    return {"success": bool(response.data)}

def _get_waitlist_position(doctor_name: str, date: str) -> int:
    """Get position on waitlist"""
    response = supabase.table("waitlist").select("id").eq(
        "doctor_name", doctor_name
    ).eq("preferred_date", date).eq("status", "waiting").execute()
    
    return len(response.data or [])

def get_waitlist_status(patient_name: str):
    """Get patient's current waitlist entries"""
    
    response = supabase.table("waitlist").select("*").eq(
        "patient_name", patient_name
    ).eq("status", "waiting").order("preferred_date").execute()
    
    entries = []
    for entry in response.data or []:
        position = _get_waitlist_position(entry["doctor_name"], entry["preferred_date"])
        entries.append({
            "id": entry["id"],
            "doctor": entry["doctor_name"],
            "date": entry["preferred_date"],
            "preferred_time": entry.get("preferred_time"),
            "position": position,
            "created_at": entry["created_at"]
        })
    
    return {
        "success": True,
        "patient": patient_name,
        "waitlist_entries": entries,
        "total": len(entries)
    }