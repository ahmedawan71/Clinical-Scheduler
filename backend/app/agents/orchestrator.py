import json
from app.config import client, DEPLOYMENT_NAME

def route_request(user_message: str):
    """
    Uses GPT to extract intent and parameters.
    """

    system_prompt = """
You are an AI orchestrator for a clinical scheduling system.
If booking an appointment, try to extract:
patient_name, patient_email, doctor_name, date, time


Return a JSON object with:
- intent: one of [check_availability, book_appointment, reschedule_appointment, send_notification]
- parameters: extracted fields if present

Rules:
- Output ONLY valid JSON
- Use null for missing fields

Example:
{
  "intent": "book_appointment",
  "parameters": {
    "doctor_name": "Dr Ahmed",
    "date": "2026-01-28",
    "time": null
  }
}
"""

    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)
