from pydantic import BaseModel

class AppointmentRequest(BaseModel):
    patient_name: str
    patient_email: str
    doctor_name: str
    date: str
    time: str
