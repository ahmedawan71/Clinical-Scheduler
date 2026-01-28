def reschedule_appointment(parameters: dict):
    return {
        "intent": "reschedule_appointment",
        "status": "rescheduled",
        "details": parameters
    }
