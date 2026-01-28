def send_notification(parameters: dict):
    return {
        "intent": "send_notification",
        "status": "sent",
        "message": parameters.get("message", "Notification sent")
    }
