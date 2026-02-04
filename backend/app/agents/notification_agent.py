from app.utils.email_service import send_email

def send_notification(parameters: dict):
    email = parameters.get("email", "")
    subject = parameters.get("subject", "Appointment Update")
    message = parameters.get("message", "Your appointment has been updated.")

    success = send_email(email, subject, message)

    return {
        "status": "sent" if success else "failed",
        "email": email
    }
