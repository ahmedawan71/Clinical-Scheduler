def send_notification(parameters: dict):
    print(f"Email sent to {parameters.get('email')}")
    return {"status": "notification_sent"}
