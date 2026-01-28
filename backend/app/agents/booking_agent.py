def book_appointment(parameters: dict):
    return {
        "intent": "book_appointment",
        "status": "confirmed",
        "details": parameters
    }
